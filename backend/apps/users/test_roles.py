"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]] · [[adr-44-field-operational-roles]] · [[adr-20-authorization-lobby]]
Docs: [[BACKEND]] · [[AUTH]]
API: [[API]]
LIVE-DOC:END"""

"""The RBAC matrix, exercised over real HTTP (adr-44).

Authorization is Django Group membership only (adr-10 rule 2): a group toggles a
role's reach; a Cognito claim never does. The lot-owner scoping (decision 3-4) is
the security-critical part — it is enforced in the backend and fails closed when a
session is unbound.
"""

import pytest
from django.contrib.auth.models import Group

from apps.clients.models import Client
from apps.users.models import AccessRequest
from apps.users.roles import (
    FEED_OPERATORS,
    FEEDLOT_OWNERS,
    FIELD_ADMINS,
    FIELD_MANAGERS,
    LOT_OWNERS,
    WORKSHOP,
)
from apps.users.services import upsert_user_from_claims

pytestmark = pytest.mark.django_db

CLAIMS = {
    "sub": "sub-role",
    "email": "role@example.com",
    "given_name": "Role",
    "family_name": "User",
}


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
    """Bind the session to a client. The AccessRequest row is auto-created at first
    login (adr-20); an admin sets `client` on it (adr-44 decision 4) — mirror that
    by updating the existing row, never creating a duplicate."""
    AccessRequest.objects.filter(user=user).update(client=client)


# --- the six groups were provisioned by migration 0007 ----------------------


def test_the_six_role_groups_exist():
    for name in (FIELD_MANAGERS, FEED_OPERATORS, LOT_OWNERS, FIELD_ADMINS, FEEDLOT_OWNERS, WORKSHOP):
        assert Group.objects.filter(name=name).exists(), name


# --- unauthenticated is rejected everywhere ---------------------------------


def test_operational_route_requires_session(client):
    assert client.get("/api/animals/").status_code in (401, 403)


def test_role_less_session_is_denied(client):
    """An authenticated session with zero role groups reaches no operational area
    (adr-20 lobby: role-less is confined)."""
    client.force_login(_user("sub-roleless"))
    assert client.get("/api/animals/").status_code == 403


# --- read matrix: who may SEE each area -------------------------------------


@pytest.mark.parametrize(
    "group,path,expected",
    [
        # livestock: everyone operational reads; workshop does not
        (FIELD_MANAGERS, "/api/animals/", 200),
        (FEED_OPERATORS, "/api/animals/", 200),
        (FIELD_ADMINS, "/api/animals/", 200),
        (FEEDLOT_OWNERS, "/api/animals/", 200),
        (WORKSHOP, "/api/animals/", 403),
        # crops/machinery: workshop reads; feed operator does not
        (WORKSHOP, "/api/pivots/", 200),
        (FIELD_MANAGERS, "/api/pivots/", 200),
        (FEEDLOT_OWNERS, "/api/pivots/", 200),
        (FEED_OPERATORS, "/api/pivots/", 403),
        (WORKSHOP, "/api/machines/", 200),
        (FEED_OPERATORS, "/api/machines/", 403),
        # ledger read: management tier only
        (FIELD_MANAGERS, "/api/ledger-entries/", 200),
        (FEEDLOT_OWNERS, "/api/ledger-entries/", 200),
        (FEED_OPERATORS, "/api/ledger-entries/", 403),
        (WORKSHOP, "/api/ledger-entries/", 403),
        # client directory: staff read; lot owner NEVER (would list every client)
        (FIELD_MANAGERS, "/api/clients/", 200),
        (FIELD_ADMINS, "/api/clients/", 200),
        (FEEDLOT_OWNERS, "/api/clients/", 200),
        (LOT_OWNERS, "/api/clients/", 403),
        (WORKSHOP, "/api/clients/", 403),
    ],
)
def test_read_matrix(client, group, path, expected):
    user = _in(_user(f"sub-read-{group}-{path}"), group)
    client.force_login(user)
    assert client.get(path).status_code == expected


# --- write matrix: who may CREATE in each area ------------------------------


@pytest.mark.parametrize(
    "group,path,denied",
    [
        # feed operator may serve feed but not write the livestock catalog
        (FEED_OPERATORS, "/api/animals/", True),
        (FIELD_MANAGERS, "/api/animals/", False),
        # only field manager + admin write feed deliveries; operator cannot
        (FEED_OPERATORS, "/api/feed-deliveries/", True),
        (FIELD_ADMINS, "/api/feed-deliveries/", False),
        # workshop writes crops; feedlot owner (read-only observer) cannot
        (FEEDLOT_OWNERS, "/api/pivots/", True),
        (WORKSHOP, "/api/pivots/", False),
    ],
)
def test_write_matrix_permission_layer(client, group, path, denied):
    """A denied writer is stopped at the permission layer (403); an allowed writer
    passes it and reaches serializer validation (400 on the empty body), never 403."""
    user = _in(_user(f"sub-write-{group}-{path}"), group)
    client.force_login(user)
    status = client.post(path, {}, content_type="application/json").status_code
    if denied:
        assert status == 403
    else:
        assert status != 403


# --- admins is the standing superset (adr-10) -------------------------------


def test_admins_reads_every_area(client):
    user = _in(_user("sub-admin-super"), "admins")
    client.force_login(user)
    for path in ("/api/animals/", "/api/pivots/", "/api/machines/", "/api/ledger-entries/", "/api/clients/"):
        assert client.get(path).status_code == 200, path


# --- lot-owner per-client scoping: the security-critical path (decision 3-4) -


def test_lot_owner_reads_only_its_own_client(client):
    own = _client_row(name="Own SA")
    other = _client_row(name="Other SA")
    user = _in(_user("sub-lotowner"), LOT_OWNERS)
    _bind(user, own)
    client.force_login(user)

    assert client.get(f"/api/clients/{own.pk}/account/").status_code == 200
    # Another client's account is invisible — scoping is enforced in the backend.
    assert client.get(f"/api/clients/{other.pk}/account/").status_code == 403


def test_lot_owner_reads_only_its_own_metrics(client):
    own = _client_row(name="Own Metrics")
    other = _client_row(name="Other Metrics")
    user = _in(_user("sub-lotowner-metrics"), LOT_OWNERS)
    _bind(user, own)
    client.force_login(user)

    assert client.get(f"/api/clients/{own.pk}/metrics/summary/").status_code == 200
    assert client.get(f"/api/clients/{other.pk}/metrics/summary/").status_code == 403


def test_unbound_lot_owner_fails_closed(client):
    """A lot-owner session with no bound client sees NOTHING — the None binding is
    the fail-closed signal, never 'all clients' (decision 4)."""
    row = _client_row(name="Some Client")
    user = _in(_user("sub-lotowner-unbound"), LOT_OWNERS)
    _bind(user, None)  # explicit: the auto-created AccessRequest has no client
    client.force_login(user)
    assert client.get(f"/api/clients/{row.pk}/account/").status_code == 403


def test_lot_owner_with_no_access_request_fails_closed(client):
    """Even with the AccessRequest row absent entirely, bound_client_id returns
    None and the session is denied — the fail-closed default (decision 4)."""
    row = _client_row(name="No AR Client")
    user = _in(_user("sub-lotowner-no-ar"), LOT_OWNERS)
    AccessRequest.objects.filter(user=user).delete()
    client.force_login(user)
    assert client.get(f"/api/clients/{row.pk}/account/").status_code == 403


def test_staff_reads_any_client_scoped_route(client):
    """A field manager is an internal role, not a tenant — reads any client's
    account without a binding (decision 5)."""
    row = _client_row(name="Any Client")
    user = _in(_user("sub-fm-scoped"), FIELD_MANAGERS)
    client.force_login(user)
    assert client.get(f"/api/clients/{row.pk}/account/").status_code == 200


def test_lot_owner_cannot_write_scoped_route(client):
    """The per-client portal is read-only; a lot owner never writes through it."""
    own = _client_row(name="RO Client")
    user = _in(_user("sub-lotowner-write"), LOT_OWNERS)
    _bind(user, own)
    client.force_login(user)
    # account is a GET-only action; POST is rejected (405) or permission-denied,
    # never accepted — a lot owner has no write path here.
    status = client.post(f"/api/clients/{own.pk}/account/", {}, content_type="application/json").status_code
    assert status in (403, 405)
