"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

"""Tests for `RouteView` (POST /api/router/route/) — RBAC + response contract
([[adr-15-chatbot-two-tier]], [[adr-10-auth]] rule 2, [[adr-16-async-mandatory]])."""

import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import IntegrityError, transaction

from apps.router.models import ESCALATE, NO_MATCH, Intent, IntentQuery
from apps.router.permissions import AI_OPERATORS_GROUP

pytestmark = pytest.mark.django_db

ROUTE = "/api/router/route/"
MODEL_BACKEND = "django.contrib.auth.backends.ModelBackend"


def _user(django_user_model, sub, groups=()):
    user = django_user_model.objects.create(sub=sub, email=f"{sub}@example.com")
    for name in groups:
        group, _ = Group.objects.get_or_create(name=name)
        user.groups.add(group)
    return user


@pytest.fixture(autouse=True)
def _cache_table():
    call_command("createcachetable")


@pytest.fixture(autouse=True)
def _mock_inference(monkeypatch):
    """Pin the view to the deterministic mock: these tests exercise the
    route contract, not Bedrock. The real-client selection and failure
    paths are covered in test_inference.py."""
    from apps.router import views
    from apps.router.inference import MockInferenceClient

    monkeypatch.setattr(views, "get_inference_client", MockInferenceClient)


def test_admins_member_reaches_endpoint(client, django_user_model):
    user = _user(django_user_model, "admin-1", groups=["admins"])
    Intent.objects.create(phrase="log out", target="/accounts/logout/", order=1)
    client.force_login(user, backend=MODEL_BACKEND)
    response = client.post(ROUTE, {"utterance": "please log me out"}, content_type="application/json")
    assert response.status_code == 200


def test_ai_operators_member_reaches_endpoint(client, django_user_model):
    user = _user(django_user_model, "operator-1", groups=[AI_OPERATORS_GROUP])
    Intent.objects.create(phrase="log out", target="/accounts/logout/", order=1)
    client.force_login(user, backend=MODEL_BACKEND)
    response = client.post(ROUTE, {"utterance": "log me out"}, content_type="application/json")
    assert response.status_code == 200


def test_plain_authenticated_user_forbidden(client, django_user_model):
    user = _user(django_user_model, "plain-1")
    client.force_login(user, backend=MODEL_BACKEND)
    response = client.post(ROUTE, {"utterance": "log me out"}, content_type="application/json")
    assert response.status_code == 403


def test_unauthenticated_rejected(client):
    response = client.post(ROUTE, {"utterance": "log me out"}, content_type="application/json")
    assert response.status_code in (401, 403)


def test_no_match_outcome(client, django_user_model):
    user = _user(django_user_model, "admin-2", groups=["admins"])
    client.force_login(user, backend=MODEL_BACKEND)
    response = client.post(ROUTE, {"utterance": "gibberish"}, content_type="application/json")
    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == NO_MATCH
    assert "action" not in body
    assert "query_id" in body


def test_escalate_outcome(client, django_user_model, monkeypatch):
    user = _user(django_user_model, "admin-3", groups=["admins"])
    client.force_login(user, backend=MODEL_BACKEND)
    from apps.router import inference

    monkeypatch.setattr(inference.MockInferenceClient, "choose", lambda self, u, m: (ESCALATE, 1.0))
    response = client.post(ROUTE, {"utterance": "help me"}, content_type="application/json")
    assert response.status_code == 200
    assert response.json()["outcome"] == "Escalate"


def test_action_outcome_shape(client, django_user_model):
    user = _user(django_user_model, "admin-4", groups=["admins"])
    Intent.objects.create(phrase="log out", target="/accounts/logout/", kind="confirm", order=1)
    client.force_login(user, backend=MODEL_BACKEND)
    response = client.post(ROUTE, {"utterance": "log me out"}, content_type="application/json")
    body = response.json()
    assert response.status_code == 200
    assert body["outcome"] == "Action"
    assert body["action"] == {"kind": "confirm", "target": "/accounts/logout/", "label": "log out"}


def test_hard_reject_outside_enum(client, django_user_model, monkeypatch):
    user = _user(django_user_model, "admin-6", groups=["admins"])
    client.force_login(user, backend=MODEL_BACKEND)
    from apps.router import inference

    monkeypatch.setattr(inference.MockInferenceClient, "choose", lambda self, u, m: ("not-on-menu", 1.0))
    response = client.post(ROUTE, {"utterance": "anything"}, content_type="application/json")
    assert response.status_code == 422
    assert response.json() == {"detail": "router_hard_reject"}


def test_router_disabled_returns_200_disabled_outcome(client, django_user_model, settings):
    settings.ROUTER_ENABLED = False
    user = _user(django_user_model, "admin-7", groups=["admins"])
    client.force_login(user, backend=MODEL_BACKEND)
    response = client.post(ROUTE, {"utterance": "anything"}, content_type="application/json")
    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == "disabled"
    assert "query_id" in body
    assert IntentQuery.objects.filter(user=user, choice="disabled").exists()


def test_throttled_burst_returns_429_and_audit_row(client, django_user_model, settings):
    settings.THROTTLE_COOLDOWN_SECONDS = 60
    user = _user(django_user_model, "admin-8", groups=["admins"])
    Intent.objects.create(phrase="log out", target="/accounts/logout/", order=1)
    client.force_login(user, backend=MODEL_BACKEND)

    first = client.post(ROUTE, {"utterance": "log me out"}, content_type="application/json")
    second = client.post(ROUTE, {"utterance": "log me out"}, content_type="application/json")

    assert first.status_code == 200
    assert second.status_code == 429
    assert IntentQuery.objects.filter(user=user, choice="throttled").exists()


def test_rate_blocked_user_gets_bare_429_no_inference(client, django_user_model, monkeypatch):
    """#371: a user already marked rate-blocked gets a bare 429 — no body
    detail, no inference call, audited as `choice="rate_blocked"`."""
    from apps.router import views

    user = _user(django_user_model, "admin-15", groups=["admins"])
    client.force_login(user, backend=MODEL_BACKEND)

    async def _always_blocked(user_id):
        return True

    monkeypatch.setattr(views, "_is_rate_blocked", _always_blocked)

    called = {"inference": False}

    def _fail_if_called(*args, **kwargs):
        called["inference"] = True
        raise AssertionError("inference must not be called for a rate-blocked user")

    monkeypatch.setattr(views, "get_inference_client", _fail_if_called)

    response = client.post(ROUTE, {"utterance": "log me out"}, content_type="application/json")

    assert response.status_code == 429
    assert response.content == b""
    assert called["inference"] is False
    assert IntentQuery.objects.filter(user=user, choice="rate_blocked").exists()


def test_permission_denied_authenticated_non_member_writes_audit_row(client, django_user_model):
    user = _user(django_user_model, "plain-2")
    client.force_login(user, backend=MODEL_BACKEND)
    response = client.post(ROUTE, {"utterance": "log me out"}, content_type="application/json")
    assert response.status_code == 403
    assert IntentQuery.objects.filter(user=user, choice="permission_denied").exists()


def test_unauthenticated_writes_no_audit_row(client):
    response = client.post(ROUTE, {"utterance": "log me out"}, content_type="application/json")
    assert response.status_code in (401, 403)
    assert IntentQuery.objects.count() == 0


def test_no_store_header(client, django_user_model):
    user = _user(django_user_model, "admin-9", groups=["admins"])
    client.force_login(user, backend=MODEL_BACKEND)
    response = client.post(ROUTE, {"utterance": "log me out"}, content_type="application/json")
    assert response["Cache-Control"] == "no-store"


def test_hard_reject_writes_audit_row_with_raw_choice(client, django_user_model, monkeypatch):
    """[[adr-15-chatbot-two-tier]] rule 2: a hard reject is logged as a fault,
    never repaired, never defaulted — the audit row keeps the raw off-menu
    choice and no `chosen_intent`."""
    user = _user(django_user_model, "admin-10", groups=["admins"])
    client.force_login(user, backend=MODEL_BACKEND)
    from apps.router import inference

    monkeypatch.setattr(inference.MockInferenceClient, "choose", lambda self, u, m: ("not-on-menu", 1.0))
    response = client.post(ROUTE, {"utterance": "anything"}, content_type="application/json")
    assert response.status_code == 422

    row = IntentQuery.objects.get(user=user)
    assert row.choice == "not-on-menu"
    assert row.chosen_intent is None


def test_gated_intent_not_offered_is_hard_rejected_even_if_model_names_it(client, django_user_model, monkeypatch):
    """[[adr-15-chatbot-two-tier]] rules 2/3: permission filtering happens
    before inference and narrows the enum — even if the model names a
    phrase belonging to a gated intent the user is not offered, it is a
    hard reject, never repaired to the gated action."""
    gated_group, _ = Group.objects.get_or_create(name="secret-ops")
    Intent.objects.create(phrase="wipe database", target="/admin/wipe/", order=1, group=gated_group)
    user = _user(django_user_model, "admin-11", groups=["admins"])
    client.force_login(user, backend=MODEL_BACKEND)
    from apps.router import inference

    monkeypatch.setattr(inference.MockInferenceClient, "choose", lambda self, u, m: ("wipe database", 1.0))
    response = client.post(ROUTE, {"utterance": "anything"}, content_type="application/json")
    assert response.status_code == 422
    assert response.json() == {"detail": "router_hard_reject"}


def test_menu_offered_in_audit_row_excludes_gated_intents(client, django_user_model):
    gated_group, _ = Group.objects.get_or_create(name="secret-ops-2")
    Intent.objects.create(phrase="wipe database", target="/admin/wipe/", order=1, group=gated_group)
    Intent.objects.create(phrase="log out", target="/accounts/logout/", order=2)
    user = _user(django_user_model, "admin-12", groups=["admins"])
    client.force_login(user, backend=MODEL_BACKEND)
    response = client.post(ROUTE, {"utterance": "log me out"}, content_type="application/json")
    assert response.status_code == 200

    row = IntentQuery.objects.get(user=user)
    phrases = [entry["phrase"] for entry in row.menu_offered]
    assert "wipe database" not in phrases
    assert "log out" in phrases


def test_inference_failure_degrades_to_503_with_audit_row(client, django_user_model, monkeypatch):
    """#253 decision 4: a Bedrock failure degrades the router surface only —
    503 router_unavailable with its audit row, never a backend crash and
    never a repaired/defaulted choice."""
    from botocore.exceptions import ClientError

    from apps.router import views

    class _FailingClient:
        model_id = "failing-model"

        def choose(self, utterance, menu):
            raise ClientError({"Error": {"Code": "AccessDeniedException"}}, "Converse")

    monkeypatch.setattr(views, "get_inference_client", _FailingClient)
    user = _user(django_user_model, "admin-14", groups=["admins"])
    Intent.objects.create(phrase="log out", target="/accounts/logout/", order=1)
    client.force_login(user, backend=MODEL_BACKEND)
    response = client.post(ROUTE, {"utterance": "log me out"}, content_type="application/json")

    assert response.status_code == 503
    assert response.json()["detail"] == "router_unavailable"
    assert response["Cache-Control"] == "no-store"
    row = IntentQuery.objects.get(user=user)
    assert row.choice == "unavailable"
    assert row.chosen_intent is None


def test_phrase_collision_rejected_before_reaching_view():
    """SECURITY #266: the two-row phrase collision this test guarded against can
    no longer reach the view — `Intent.phrase` is unique, so seeding a second
    row with a duplicate phrase is rejected DB-side at data-entry time. The
    view-level "resolves to the gated row" failure mode is now structurally
    impossible ([[adr-15-chatbot-two-tier]] rule 2)."""
    gated_group, _ = Group.objects.get_or_create(name="secret-ops-4")
    Intent.objects.create(phrase="log out", target="/accounts/logout/", kind="confirm", order=1)
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            Intent.objects.create(
                phrase="log out", target="/admin/secret-panel/", order=2, group=gated_group
            )


def test_unauthorized_user_gets_only_reserved_outcomes(client, django_user_model):
    """A router-eligible user (admins) with zero visible registry intents —
    every Intent is gated to a group they lack — sees only the two reserved
    outcomes, never a degenerate empty menu ([[adr-15-chatbot-two-tier]])."""
    gated_group, _ = Group.objects.get_or_create(name="secret-ops-3")
    Intent.objects.create(phrase="wipe database", target="/admin/wipe/", order=1, group=gated_group)
    user = _user(django_user_model, "admin-13", groups=["admins"])
    client.force_login(user, backend=MODEL_BACKEND)
    response = client.post(ROUTE, {"utterance": "anything"}, content_type="application/json")
    assert response.status_code == 200

    row = IntentQuery.objects.get(user=user)
    phrases = {entry["phrase"] for entry in row.menu_offered}
    assert phrases == {NO_MATCH, ESCALATE}
