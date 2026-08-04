"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

"""Pure menu-construction for the chatbot router choosing tier.

build_menu(user) returns the permission-filtered closed menu, plus the two
reserved outcomes (NO_MATCH, ESCALATE), which are always present regardless
of registry contents (#104). An active Intent reaches the menu three ways:

- **ungated** — its group gate is unset, so every user sees it;
- **group-matched** — its gate is one of the user's Django Groups;
- **admins-superset** — the user belongs to `admins`, the standing app-wide
  superset (#135), which short-circuits the gate entirely and yields every
  active row. Same authority the rest of the app already grants that group
  (roles.py / GroupMatrixPermission, and signals.py mirroring it into
  is_staff/is_superuser) — the menu is not inventing a privilege here.

The filter is a Django-side authorization decision taken before the model is
invoked, so the router only ever narrows within an already-authorized set
([[adr-15-chatbot-two-tier]] rules 2/3). `is_active` is registry state, not
permission, and no membership reaches past it. No degenerate case exists:
even a fresh Cognito user with zero group memberships gets a menu with at
least the two reserved members ([[adr-15-chatbot-two-tier]]).
"""

from django.db.models import Q

from apps.router.models import ESCALATE, NO_MATCH, Intent
from apps.users.permissions import ADMINS_GROUP


def build_menu(user):
    """Return (menu, by_phrase): the ordered menu visible to `user`, and a
    phrase->Intent map built from the SAME permission-filtered queryset
    ([[adr-15-chatbot-two-tier]] rules 2/3) — the sole source of truth for
    resolving a chosen phrase to its `Intent`; no caller may re-query
    `Intent` by phrase text alone.

    Ordering is explicit (#94): registry intents first, ordered by
    Intent.order then pk, followed by the reserved outcomes in the fixed
    order (NO_MATCH, ESCALATE).
    """
    memberships = list(user.groups.values_list("id", "name")) if user.is_authenticated else []

    visible = Intent.objects.filter(is_active=True)
    if not any(name == ADMINS_GROUP for _group_id, name in memberships):
        group_ids = [group_id for group_id, _name in memberships]
        visible = visible.filter(Q(group__isnull=True) | Q(group_id__in=group_ids))

    intents = list(visible.order_by("order", "pk"))

    menu = [
        {"phrase": intent.phrase, "target": intent.target, "kind": intent.kind}
        for intent in intents
    ]
    menu.append({"phrase": NO_MATCH, "target": None, "kind": None})
    menu.append({"phrase": ESCALATE, "target": None, "kind": None})

    by_phrase = {}
    for intent in intents:
        by_phrase.setdefault(intent.phrase, intent)

    return menu, by_phrase
