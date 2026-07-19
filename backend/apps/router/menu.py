"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

"""Pure menu-construction for the chatbot router choosing tier.

build_menu(user) returns the permission-filtered closed menu: every active
Intent whose group gate is either unset (ungated) or one of the user's
Django Groups, plus the two reserved outcomes (NO_MATCH, ESCALATE), which
are always present regardless of registry contents (#104). No degenerate
case exists: even a fresh Cognito user with zero group memberships gets a
menu with at least the two reserved members ([[adr-15-chatbot-two-tier]]).
"""

from django.db.models import Q

from apps.router.models import ESCALATE, NO_MATCH, Intent


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
    group_ids = list(user.groups.values_list("id", flat=True)) if user.is_authenticated else []

    intents = list(
        Intent.objects.filter(is_active=True)
        .filter(Q(group__isnull=True) | Q(group_id__in=group_ids))
        .order_by("order", "pk")
    )

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
