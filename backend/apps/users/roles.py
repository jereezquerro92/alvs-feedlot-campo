"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]] · [[adr-44-field-operational-roles]] · [[adr-20-authorization-lobby]] · [[adr-03-api-and-backend]] · [[adr-45-lot-owner-assistant-access]]
Docs: [[BACKEND]] · [[AUTH]]
API: [[API]]
LIVE-DOC:END"""

"""The one place the RBAC matrix lives (adr-44 decision 1).

Every feedlot viewset references one of the area permission classes below; who
can read or write an area is decided here and nowhere else, so tuning the matrix
is editing this file — never hunting permissions across ~18 apps. Authorization
is read from Django Group membership only, never a Cognito claim (adr-10 rule 2).
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.users.models import AccessRequest
from apps.users.permissions import ADMINS_GROUP

# --- the six operational role groups (adr-44) --------------------------------
# Names are the GLOSSARY canonical forms; created by migration 0007.
FIELD_MANAGERS = "field_managers"
FEED_OPERATORS = "feed_operators"
LOT_OWNERS = "lot_owners"
FIELD_ADMINS = "field_admins"
FEEDLOT_OWNERS = "feedlot_owners"
WORKSHOP = "workshop"

ROLE_GROUPS = (
    FIELD_MANAGERS,
    FEED_OPERATORS,
    LOT_OWNERS,
    FIELD_ADMINS,
    FEEDLOT_OWNERS,
    WORKSHOP,
)


class GroupMatrixPermission(BasePermission):
    """Method-split group gate (adr-44 decisions 1-2).

    A safe method (GET/HEAD/OPTIONS) needs membership in ``read_groups``; a write
    method (POST/PUT/PATCH/DELETE) needs membership in ``write_groups``. ``admins``
    always passes — it is the standing superset (adr-10). A subclass sets the two
    tuples; the check shape is shared, the group sets are not.
    """

    read_groups: tuple[str, ...] = ()
    write_groups: tuple[str, ...] = ()

    def _group_names(self, user):
        return set(user.groups.values_list("name", flat=True))

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        names = self._group_names(user)
        if ADMINS_GROUP in names:
            return True
        allowed = self.read_groups if request.method in SAFE_METHODS else self.write_groups
        return bool(names.intersection(allowed))


# --- per-area classes: the matrix (adr-44 decision 1) ------------------------
# read = who may see the area; write = who may create/edit. admins passes always.


class LivestockAccess(GroupMatrixPermission):
    read_groups = (FIELD_MANAGERS, FEED_OPERATORS, FIELD_ADMINS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS,)


class FeedCatalogAccess(GroupMatrixPermission):
    read_groups = (FIELD_MANAGERS, FEED_OPERATORS, FIELD_ADMINS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS, FIELD_ADMINS)


class FeedDeliveryAccess(GroupMatrixPermission):
    """Merchandise into feed stock: the administrative role loads it (adr-44)."""

    read_groups = (FIELD_MANAGERS, FIELD_ADMINS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS, FIELD_ADMINS)


class FeedExecutionAccess(GroupMatrixPermission):
    """Serving feed at the mixer: the operative role executes it (adr-44)."""

    read_groups = (FIELD_MANAGERS, FEED_OPERATORS, FIELD_ADMINS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS, FEED_OPERATORS)


class FeedyardAccess(GroupMatrixPermission):
    """Mixer planning/monitoring: pens, rations, loading orders, bunk scores, placement."""

    read_groups = (FIELD_MANAGERS, FEED_OPERATORS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS, FEED_OPERATORS)


class SanitaryAccess(GroupMatrixPermission):
    read_groups = (FIELD_MANAGERS, FEED_OPERATORS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS,)


class InventoryAccess(GroupMatrixPermission):
    """Merchandise into general input stock: the administrative role loads it (adr-44)."""

    read_groups = (FIELD_MANAGERS, FIELD_ADMINS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS, FIELD_ADMINS)


class WeatherAccess(GroupMatrixPermission):
    read_groups = (FIELD_MANAGERS, FIELD_ADMINS, FEEDLOT_OWNERS, WORKSHOP)
    write_groups = (FIELD_MANAGERS, FIELD_ADMINS)


class CropsAccess(GroupMatrixPermission):
    """Alfalfa: pivots, crops, cuttings, field tasks — the workshop role (adr-44)."""

    read_groups = (FIELD_MANAGERS, WORKSHOP, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS, WORKSHOP)


class MachineryAccess(GroupMatrixPermission):
    """Machinery use + maintenance + fuel — the workshop role (adr-44)."""

    read_groups = (FIELD_MANAGERS, WORKSHOP, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS, WORKSHOP)


class ExpensesAccess(GroupMatrixPermission):
    """Extra charges (labor/fuel/machinery) billed to a client's account — the
    field manager's "carga de deudas" via events, never a manual ledger debit
    (adr-44 decision 6). The workshop role also loads fuel/machinery charges."""

    read_groups = (FIELD_MANAGERS, WORKSHOP, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS, WORKSHOP)


class LedgerReadAccess(GroupMatrixPermission):
    """Ledger entries are immutable and read-only over HTTP (adr-25 rule 1)."""

    read_groups = (FIELD_MANAGERS, FEEDLOT_OWNERS)
    write_groups = ()


class LedgerWriteAccess(GroupMatrixPermission):
    """Payments and their imputation — the field manager's "carga de deudas" (adr-44 decision 6)."""

    read_groups = (FIELD_MANAGERS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS,)


class MarketAccess(GroupMatrixPermission):
    read_groups = (FIELD_MANAGERS, FEED_OPERATORS, FIELD_ADMINS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS, FIELD_ADMINS)


class FxAccess(GroupMatrixPermission):
    read_groups = (FIELD_MANAGERS, FIELD_ADMINS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS, FIELD_ADMINS)


class TraceabilityAccess(GroupMatrixPermission):
    read_groups = (FIELD_MANAGERS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS,)


class NotificationsAccess(GroupMatrixPermission):
    read_groups = (FIELD_MANAGERS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS,)


class AdvisorAccess(GroupMatrixPermission):
    """Generative advisor reports over a client's metrics (adr-27) — an internal
    management analysis surface, filtered by ``?client=`` not a route pk, so a lot
    owner never reaches it (they read their own metrics/balance, not the analyst's
    text). Read: management tier; write (generate = paid inference): field manager."""

    read_groups = (FIELD_MANAGERS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS,)


class AssistantAccess(GroupMatrixPermission):
    """The conversational asesor over a client's data (adr-35).

    Staff (field manager, feedlot owner) read any client; a field manager also
    writes (asks). A ``lot_owners`` portal session may ALSO use the asesor — but
    ONLY over the client bound to its ``AccessRequest`` (adr-27 rule 2). This is
    the third client-keyed surface the portal reaches, authorized by adr-45, the
    additive ADR that extends the "exactamente" route list of adr-44 decision 3
    (métricas + cuenta + asesor) by the vehicle that decision requires — a new
    ADR, never a local exception (adr-20 rule 2). The asesor is read-only over
    domain data (adr-35 decision 1): asking never mutates a client's records, so
    a scoped read/ask surface does not widen the portal's read-only posture
    beyond its own tenant.

    The confinement fails closed three ways, all keyed on the bound client
    (decision 4): here the requested ``client`` (query param or POST body) must
    equal the bound client; ``has_object_permission`` re-checks the conversation's
    client on a detail route; and the viewset queryset filters lists to the bound
    client. An unbound lot-owner session reaches nothing.
    """

    read_groups = (FIELD_MANAGERS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS,)

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        names = self._group_names(user)
        if ADMINS_GROUP in names:
            return True
        allowed = self.read_groups if request.method in SAFE_METHODS else self.write_groups
        if names.intersection(allowed):
            return True
        # Lot-owner portal: read and ask, confined to the bound client.
        if LOT_OWNERS in names:
            bound = bound_client_id(user)
            if bound is None:
                return False  # unbound → fail closed (adr-44 decision 4)
            target = _requested_client_id(request)
            # A detail route (messages) carries no client key; the queryset scope
            # and has_object_permission enforce the boundary there. On list/create
            # the client is present and must match the binding.
            return target is None or target == bound
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        names = self._group_names(user)
        if ADMINS_GROUP in names:
            return True
        allowed = self.read_groups if request.method in SAFE_METHODS else self.write_groups
        if names.intersection(allowed):
            return True
        if LOT_OWNERS in names:
            bound = bound_client_id(user)
            return bound is not None and getattr(obj, "client_id", None) == bound
        return False


class ClientDirectoryAccess(GroupMatrixPermission):
    """The client roster (list + CRUD). A lot owner NEVER reaches it — it would
    list every client (adr-44 decision 3). Their portal is the scoped surface below."""

    read_groups = (FIELD_MANAGERS, FIELD_ADMINS, FEEDLOT_OWNERS)
    write_groups = (FIELD_MANAGERS,)


def bound_client_id(user):
    """The single Client a session is confined to, or None (adr-44 decision 4).

    Set by an admin on the user's AccessRequest; a lot owner with no binding sees
    nothing — the None is the fail-closed signal, never "all clients".
    """
    row = AccessRequest.objects.filter(user=user).only("client_id").first()
    return row.client_id if row else None


def _route_client_id(view):
    raw = view.kwargs.get("pk", view.kwargs.get("client_id"))
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _requested_client_id(request):
    """The client a request targets via ``?client=`` or a JSON ``client`` body key.

    Used to confine a lot-owner portal session on the query/body-keyed surfaces
    (the asesor), where the route pk is the conversation, not the client (adr-44
    decision 3). Returns None when absent/unparseable — the caller decides what
    None means (a list is scoped by the queryset; a detail route rides the object).
    """
    raw = request.query_params.get("client")
    if raw is None:
        data = getattr(request, "data", None)
        if isinstance(data, dict):
            raw = data.get("client")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


# Staff groups that read the asesor unscoped (any client); a session holding one of
# these is never confined, even if it also holds ``lot_owners`` (decision 5).
ASSISTANT_STAFF_GROUPS = (FIELD_MANAGERS, FEEDLOT_OWNERS)


def is_assistant_portal_session(user):
    """True for a lot-owner-only asesor session — one that must be confined to its
    bound client. False for staff/admin (unscoped) and for anonymous sessions.

    A user who also holds a staff asesor group (or ``admins``) is NOT confined:
    they are an internal role, not a tenant (adr-44 decision 5).
    """
    if not (user and user.is_authenticated):
        return False
    names = set(user.groups.values_list("name", flat=True))
    if ADMINS_GROUP in names or names.intersection(ASSISTANT_STAFF_GROUPS):
        return False
    return LOT_OWNERS in names


class ClientScopedReadPermission(BasePermission):
    """The per-client read portal (adr-44 decision 3).

    Staff in ``staff_read_groups`` (and ``admins``) read any client — they are
    internal roles, not tenants (decision 5). A ``lot_owners`` session reads ONLY
    the client bound to its AccessRequest, and only for safe methods; a mismatch
    or an unbound session is rejected (fails closed, decision 4). The whole surface
    is read-only — a write is granted to no one but ``admins`` here.
    """

    staff_read_groups = (FIELD_MANAGERS, FEEDLOT_OWNERS, FIELD_ADMINS, FEED_OPERATORS)

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        names = set(user.groups.values_list("name", flat=True))
        if ADMINS_GROUP in names:
            return True
        if request.method not in SAFE_METHODS:
            return False
        if names.intersection(self.staff_read_groups):
            return True
        if LOT_OWNERS in names:
            bound = bound_client_id(user)
            if bound is None:
                return False
            return _route_client_id(view) == bound
        return False
