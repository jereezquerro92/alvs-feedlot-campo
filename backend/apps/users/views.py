"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]] · [[adr-03-api-and-backend]]
Docs: [[BACKEND]] · [[AUTH]]
API: [[API]]
LIVE-DOC:END"""

import json
import logging
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import login, logout
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users import oidc
from apps.users.permissions import IsInAdminsGroup
from apps.users.serializers import UserSerializer
from apps.users.services import upsert_user_from_claims

logger = logging.getLogger(__name__)

MODEL_BACKEND = "django.contrib.auth.backends.ModelBackend"
DEV_BACKEND = "apps.users.backends.DevLoginBackend"

COGNITO_REQUIRED_SETTINGS = (
    "COGNITO_CLIENT_ID",
    "COGNITO_DOMAIN",
    "COGNITO_USER_POOL_ID",
)


def _missing_cognito_settings():
    return [name for name in COGNITO_REQUIRED_SETTINGS if not getattr(settings, name, "")]


def _no_store(response):
    response["Cache-Control"] = "no-store"
    return response


def set_theme_cookie(response, blob):
    """Mirror a user's theme_config blob into the non-HttpOnly `theme` cookie
    ([[DESIGN-SYSTEM]]) so Astro SSR can render it with no flash."""
    response.set_cookie(
        "theme",
        quote(json.dumps(blob), safe=""),
        max_age=31536000,
        path="/",
        samesite="Lax",
        secure=settings.CSRF_COOKIE_SECURE,
        httponly=False,
    )
    return response


def _callback_uri(request):
    return request.build_absolute_uri(reverse("accounts:callback"))


class LoginView(View):
    def get(self, request):
        missing = _missing_cognito_settings()
        if missing:
            if settings.DEBUG and settings.AUTH_DEV_MODE:
                logger.info("Cognito not configured; DEBUG dev auth active, routing to dev-login")
                return _no_store(redirect("accounts:dev-login"))
            logger.error("Cognito is not configured; missing: %s", ", ".join(missing))
            return _no_store(
                render(request, "users/cognito_not_configured.html", {"missing": missing}, status=500)
            )
        state = oidc.new_state()
        request.session[oidc.STATE_SESSION_KEY] = state
        url = oidc.build_authorize_url(_callback_uri(request), state)
        return _no_store(redirect(url))


class CallbackView(View):
    def get(self, request):
        expected = request.session.pop(oidc.STATE_SESSION_KEY, None)
        state = request.GET.get("state")
        if not expected or state != expected:
            return _no_store(HttpResponseBadRequest("invalid state"))
        code = request.GET.get("code")
        if not code:
            return _no_store(HttpResponseBadRequest("missing code"))
        try:
            tokens = oidc.exchange_code(code, _callback_uri(request))
            claims = oidc.verify_id_token(tokens["id_token"])
        except Exception:
            logger.exception("OIDC callback failed during token exchange/verification")
            return _no_store(
                HttpResponseBadRequest(
                    "Authentication failed while verifying your login with Cognito. "
                    "Please try logging in again; if this persists, contact an operator."
                )
            )
        # The ID token does not carry federated-IdP attributes (e.g. `picture`);
        # only /oauth2/userInfo does. Best-effort: a failure here must not
        # break login, it only means the avatar falls back to initials.
        try:
            userinfo = oidc.fetch_userinfo(tokens["access_token"])
            claims = {**claims, **userinfo}
        except Exception:
            logger.warning("OIDC userInfo fetch failed; continuing with ID token claims only", exc_info=True)
        logger.info("OIDC callback claims ready to mirror; keys: %s", sorted(claims.keys()))
        user = upsert_user_from_claims(claims)
        login(request, user, backend=MODEL_BACKEND)
        response = _no_store(redirect(settings.LOGIN_REDIRECT_URL))
        return set_theme_cookie(response, user.theme_config)


class LogoutView(View):
    def post(self, request):
        logout(request)
        if not settings.COGNITO_DOMAIN:
            # Dev/local: no Cognito to sign out of — land back on the app.
            return _no_store(redirect(settings.LOGOUT_REDIRECT_URL))
        url = oidc.build_logout_url(request.build_absolute_uri(settings.LOGOUT_REDIRECT_URL))
        return _no_store(redirect(url))


class DevLoginView(View):
    def get(self, request):
        email = request.GET.get("email", "dev@example.com")
        claims = {
            "sub": f"dev-{email}",
            "email": email,
            "given_name": "Dev",
            "family_name": "User",
        }
        user = upsert_user_from_claims(claims)
        login(request, user, backend=DEV_BACKEND)
        response = _no_store(redirect(settings.LOGIN_REDIRECT_URL))
        return set_theme_cookie(response, user.theme_config)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = UserSerializer(request.user).data
        return _no_store(Response(data))

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = _no_store(Response(serializer.data))
        if "theme_config" in request.data:
            set_theme_cookie(response, serializer.instance.theme_config)
        return response


class RestrictedView(APIView):
    permission_classes = [IsAuthenticated, IsInAdminsGroup]

    def get(self, request):
        return _no_store(Response({"detail": "ok"}))
