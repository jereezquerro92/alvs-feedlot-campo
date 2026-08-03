"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-35-conversational-assistant]] · [[adr-44-field-operational-roles]] · [[adr-27-advisors-generative]] · [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
API: [[API]]
LIVE-DOC:END"""

"""The asesor's tenant boundary over real HTTP (adr-44 decision 3, adr-27 rule 2).

A ``lot_owners`` portal session may use the conversational asesor, but ONLY over
the single client bound to its AccessRequest — never another client's threads or
turns. This is a tenant-isolation boundary, so it is proven end-to-end at the
permission layer, not just at the service. Staff (field manager, feedlot owner)
stay unscoped. Every message POST runs against MockAssistantClient (DEBUG), never
the network (adr-35 decision 5).
"""

import pytest
from django.contrib.auth.models import Group
from django.test import override_settings

from apps.assistant.models import Conversation
from apps.clients.models import Client
from apps.users.models import AccessRequest
from apps.users.roles import FEEDLOT_OWNERS, FIELD_MANAGERS, LOT_OWNERS
from apps.users.services import upsert_user_from_claims

pytestmark = pytest.mark.django_db

CLAIMS = {
    "sub": "sub-asesor",
    "email": "asesor@example.com",
    "given_name": "Asesor",
    "family_name": "User",
}

# DEBUG=True forces MockAssistantClient — a posted turn never hits the network
# (adr-35 decision 5), the same gate the service tests use.
debug = override_settings(DEBUG=True)


def _user(sub, **overrides):
    return upsert_user_from_claims({**CLAIMS, **overrides, "sub": sub})


def _in(user, *group_names):
    for name in group_names:
        user.groups.add(Group.objects.get(name=name))
    return user


def _client_row(name="Acme", kind="boarding"):
    # Account is auto-created by a post_save signal — do not create a second.
    return Client.objects.create(name=name, kind=kind)


def _bind(user, client):
    """Mirror an admin setting AccessRequest.client (adr-44 decision 4) on the row
    the login flow auto-created — never create a duplicate."""
    AccessRequest.objects.filter(user=user).update(client=client)


def _thread(client, title="Consulta"):
    return Conversation.objects.create(client=client, title=title)


# --- unauthenticated and role-less are rejected -----------------------------


def test_asesor_requires_a_session(client):
    assert client.get("/api/conversations/").status_code in (401, 403)


def test_role_less_session_is_denied(client):
    client.force_login(_user("sub-roleless-asesor"))
    assert client.get("/api/conversations/").status_code == 403


# --- lot owner: confined to its bound client (decision 3) --------------------


def test_lot_owner_lists_only_its_own_client_threads(client):
    own = _client_row(name="Own SA")
    other = _client_row(name="Other SA")
    _thread(own, "mía")
    _thread(other, "ajena")
    user = _in(_user("sub-lo-list"), LOT_OWNERS)
    _bind(user, own)
    client.force_login(user)

    body = client.get("/api/conversations/").json()
    rows = body.get("results", body) if isinstance(body, dict) else body
    client_ids = {row["client"] for row in rows}
    assert client_ids == {own.pk}  # never the other tenant's thread


def test_lot_owner_creates_a_thread_for_its_own_client(client):
    own = _client_row(name="Own Create")
    user = _in(_user("sub-lo-create-own"), LOT_OWNERS)
    _bind(user, own)
    client.force_login(user)

    res = client.post(
        "/api/conversations/", {"client": own.pk, "title": "hola"},
        content_type="application/json",
    )
    assert res.status_code == 201
    assert res.json()["client"] == own.pk


def test_lot_owner_cannot_create_a_thread_for_another_client(client):
    own = _client_row(name="Own X")
    other = _client_row(name="Other X")
    user = _in(_user("sub-lo-create-other"), LOT_OWNERS)
    _bind(user, own)
    client.force_login(user)

    res = client.post(
        "/api/conversations/", {"client": other.pk, "title": "intruso"},
        content_type="application/json",
    )
    assert res.status_code == 403


def test_lot_owner_cannot_reach_another_clients_thread(client):
    own = _client_row(name="Own Read")
    other = _client_row(name="Other Read")
    foreign = _thread(other, "ajena")
    user = _in(_user("sub-lo-retrieve"), LOT_OWNERS)
    _bind(user, own)
    client.force_login(user)

    # Out of the portal queryset entirely → 404 (never a body leak).
    assert client.get(f"/api/conversations/{foreign.pk}/").status_code == 404
    assert client.get(f"/api/conversations/{foreign.pk}/messages/").status_code == 404


@debug
def test_lot_owner_asks_on_its_own_thread(client):
    own = _client_row(name="Own Ask")
    thread = _thread(own)
    user = _in(_user("sub-lo-ask-own"), LOT_OWNERS)
    _bind(user, own)
    client.force_login(user)

    res = client.post(
        f"/api/conversations/{thread.pk}/messages/", {"text": "¿cuántas cabezas?"},
        content_type="application/json",
    )
    assert res.status_code == 201
    assert res.json()["role"] == "assistant"


@debug
def test_lot_owner_cannot_ask_on_another_clients_thread(client):
    own = _client_row(name="Own Ask2")
    other = _client_row(name="Other Ask2")
    foreign = _thread(other)
    user = _in(_user("sub-lo-ask-other"), LOT_OWNERS)
    _bind(user, own)
    client.force_login(user)

    res = client.post(
        f"/api/conversations/{foreign.pk}/messages/", {"text": "colarme"},
        content_type="application/json",
    )
    assert res.status_code in (403, 404)


# --- lot owner fails closed when unbound (decision 4) -----------------------


def test_unbound_lot_owner_reaches_nothing(client):
    own = _client_row(name="Unbound Target")
    _thread(own)
    user = _in(_user("sub-lo-unbound"), LOT_OWNERS)
    _bind(user, None)  # explicit: the auto-created AccessRequest has no client
    client.force_login(user)

    # The None binding is fail-closed at the permission layer: the list itself is
    # denied (403), not served as an empty page, and a create is rejected too.
    assert client.get("/api/conversations/").status_code == 403
    res = client.post(
        "/api/conversations/", {"client": own.pk, "title": "x"},
        content_type="application/json",
    )
    assert res.status_code == 403


def test_lot_owner_with_no_access_request_fails_closed(client):
    own = _client_row(name="No AR Target")
    user = _in(_user("sub-lo-no-ar"), LOT_OWNERS)
    AccessRequest.objects.filter(user=user).delete()
    client.force_login(user)
    res = client.post(
        "/api/conversations/", {"client": own.pk, "title": "x"},
        content_type="application/json",
    )
    assert res.status_code == 403


# --- staff stay unscoped (decision 5) ---------------------------------------


def test_field_manager_reaches_any_client_thread(client):
    a = _client_row(name="Client A")
    b = _client_row(name="Client B")
    _thread(a)
    _thread(b)
    user = _in(_user("sub-fm-asesor"), FIELD_MANAGERS)
    client.force_login(user)

    body = client.get("/api/conversations/").json()
    rows = body.get("results", body) if isinstance(body, dict) else body
    assert {row["client"] for row in rows} == {a.pk, b.pk}  # not scoped

    res = client.post(
        "/api/conversations/", {"client": b.pk, "title": "staff"},
        content_type="application/json",
    )
    assert res.status_code == 201


def test_feedlot_owner_reads_but_does_not_ask(client):
    """The feedlot owner is a read-only observer of the asesor: it lists threads
    but cannot create one (write = field manager only)."""
    a = _client_row(name="Obs Client")
    _thread(a)
    user = _in(_user("sub-fo-asesor"), FEEDLOT_OWNERS)
    client.force_login(user)

    assert client.get("/api/conversations/").status_code == 200
    res = client.post(
        "/api/conversations/", {"client": a.pk, "title": "obs"},
        content_type="application/json",
    )
    assert res.status_code == 403
