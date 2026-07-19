"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]] · [[adr-03-api-and-backend]]
Docs: [[BACKEND]] · [[CHATBOT]]
API: [[API]]
LIVE-DOC:END"""

"""`RouteView` — the chatbot router choosing tier's HTTP endpoint
([[adr-15-chatbot-two-tier]], [[adr-16-async-mandatory]]).

RBAC-gated, async, wired through `get_inference_client` — the real Bedrock
client in any non-DEBUG process, the deterministic mock only under DEBUG
(#253). Every request — success, hard reject, unavailable, disabled,
throttled — persists exactly one `IntentQuery` audit row.
"""

import logging

from asgiref.sync import sync_to_async
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.router.inference import get_inference_client
from apps.router.menu import build_menu
from apps.router.models import ESCALATE, NO_MATCH, IntentQuery
from apps.router.permissions import CanUseRouter
from apps.router.rate_abuse import evaluate_rate_abuse, is_rate_blocked
from apps.router.serializers import ActionSerializer, RouteRequestSerializer
from config.throttling import CooldownThrottle

_is_rate_blocked = sync_to_async(is_rate_blocked)
_evaluate_rate_abuse = sync_to_async(evaluate_rate_abuse)

logger = logging.getLogger(__name__)


def _no_store(response):
    response["Cache-Control"] = "no-store"
    return response


def _create_audit_row(*, utterance, menu, choice, model_id, latency_ms, user, chosen_intent=None):
    return IntentQuery.objects.create(
        utterance=utterance,
        menu_offered=menu,
        choice=choice,
        chosen_intent=chosen_intent,
        model_id=model_id,
        latency_ms=latency_ms,
        user=user,
    )


_write_audit_row = sync_to_async(_create_audit_row)


@sync_to_async
def _build_menu_and_lookup(user):
    """Build the permission-filtered menu and its phrase->Intent map, both
    sourced from `build_menu`'s single permission-filtered queryset — no
    second, unscoped `Intent` re-query (SECURITY #266:
    [[adr-15-chatbot-two-tier]] rules 2/3)."""
    return build_menu(user)


class RouteView(APIView):
    """POST /api/router/route/ — takes a user utterance, returns a closed-enum outcome."""

    permission_classes = [IsAuthenticated, CanUseRouter]
    throttle_classes = [CooldownThrottle]

    async def dispatch(self, request, *args, **kwargs):
        """Async-capable dispatch ([[adr-16-async-mandatory]]).

        DRF 3.17's `APIView.dispatch` is synchronous end to end and cannot
        host an `async def` handler unmodified. This override keeps the same
        shape (initial → handler → finalize_response, same exception
        handling) but runs `self.initial()` — which does sync ORM/cache work
        via `check_permissions`/`check_throttles` — through
        `sync_to_async`, and awaits the handler when it is a coroutine
        function. No bare sync ORM/cache call runs on the event loop thread.
        """
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers

        try:
            await sync_to_async(self.initial)(request, *args, **kwargs)

            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            response = handler(request, *args, **kwargs)
            if hasattr(response, "__await__"):
                response = await response
        except Exception as exc:
            response = await sync_to_async(self.handle_exception)(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response

    async def post(self, request):
        # `self.initial()` (permission/throttle checks) already ran, wrapped
        # in `sync_to_async` by the `dispatch` override above; a reject
        # there raises before this coroutine runs, and its audit row is
        # written by the synchronous `throttled`/`permission_denied` hooks
        # below (safe: they execute inside that same sync_to_async thread).
        request_serializer = RouteRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        utterance = request_serializer.validated_data["utterance"]

        # Silent rate-abuse guard (#371, [[adr-16-async-mandatory]]): a single
        # cheap cache read, checked before any router work — never reveals why.
        if await _is_rate_blocked(request.user.pk):
            await _write_audit_row(
                utterance=utterance,
                menu=[],
                choice="rate_blocked",
                model_id="",
                latency_ms=None,
                user=request.user,
            )
            return _no_store(Response(status=429))

        if not settings.ROUTER_ENABLED:
            audit_row = await _write_audit_row(
                utterance=utterance,
                menu=[],
                choice="disabled",
                model_id="",
                latency_ms=None,
                user=request.user,
            )
            return _no_store(Response({"outcome": "disabled", "query_id": audit_row.pk}, status=200))

        menu, by_phrase = await _build_menu_and_lookup(request.user)
        client = get_inference_client()
        try:
            choice, latency_ms = await sync_to_async(client.choose)(utterance, menu)
        except (BotoCoreError, ClientError):
            # A Bedrock outage degrades the router surface only — it never
            # takes the backend down (#253 decision 4, ROUTER_ENABLED-style).
            logger.exception("router inference unavailable")
            audit_row = await _write_audit_row(
                utterance=utterance,
                menu=menu,
                choice="unavailable",
                model_id=client.model_id,
                latency_ms=None,
                user=request.user,
            )
            return _no_store(
                Response({"detail": "router_unavailable", "query_id": audit_row.pk}, status=503)
            )

        valid_phrases = {entry["phrase"] for entry in menu}
        if choice not in valid_phrases:
            await _write_audit_row(
                utterance=utterance,
                menu=menu,
                choice=choice,
                model_id=client.model_id,
                latency_ms=latency_ms,
                user=request.user,
            )
            return _no_store(Response({"detail": "router_hard_reject"}, status=422))

        chosen_intent = by_phrase.get(choice)
        audit_row = await _write_audit_row(
            utterance=utterance,
            menu=menu,
            choice=choice,
            model_id=client.model_id,
            latency_ms=latency_ms,
            user=request.user,
            chosen_intent=chosen_intent,
        )

        if choice == NO_MATCH:
            outcome, action = "NO_MATCH", None
        elif choice == ESCALATE:
            outcome, action = "Escalate", None
        else:
            outcome = "Action"
            action = {
                "kind": chosen_intent.kind if chosen_intent else "navigate",
                "target": chosen_intent.target if chosen_intent else None,
                "label": choice,
            }

        payload = {"outcome": outcome, "query_id": audit_row.pk}
        if action is not None:
            action_serializer = ActionSerializer(data=action)
            action_serializer.is_valid(raise_exception=True)
            payload["action"] = action_serializer.validated_data

        # Fired only once a request actually reached inference — the silent
        # rate-abuse guard's own evaluation (#371). Runs at the very end so
        # it never delays the response above; it never blocks *this*
        # request, only a future one from the same user.
        await _evaluate_rate_abuse(request.user.pk)

        return _no_store(Response(payload, status=200))

    def throttled(self, request, wait):
        _create_audit_row(
            utterance=(request.data or {}).get("utterance") if hasattr(request, "data") else None,
            menu=[],
            choice="throttled",
            model_id="",
            latency_ms=None,
            user=request.user,
        )
        return super().throttled(request, wait)

    def permission_denied(self, request, message=None, code=None):
        if request.user and request.user.is_authenticated:
            _create_audit_row(
                utterance=None,
                menu=[],
                choice="permission_denied",
                model_id="",
                latency_ms=None,
                user=request.user,
            )
        return super().permission_denied(request, message=message, code=code)
