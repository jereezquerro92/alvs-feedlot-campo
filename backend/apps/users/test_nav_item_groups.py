"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-44-field-operational-roles]] · [[adr-53-api-membrane]] · [[adr-54-site-menu-lock-modes]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

"""The site menu's item→groups table must not drift from the RBAC matrix.

`apps/users/roles.py` is the one home of the matrix (adr-44 rule 1) and each area
class's ``read_groups`` is exactly "who may see this area". The frontend trims its
menu with a mirror of those group names (adr-54 rule 9), which is UI convenience —
the barrier stays here (adr-44 rule 8).

The check lives on THIS side on purpose. The frontend may not know a permission
class exists (adr-53 rule 2), so it cannot be the one to compare; the server may
read the frontend's table, because the membrane's prohibition runs one way. So the
item→class binding — the knowledge that ``ledger`` is governed by
``LedgerReadAccess`` — is recorded here and nowhere in ``frontend/``.
"""

import re
from pathlib import Path

from apps.users import roles
from apps.users.permissions import ADMINS_GROUP

FRONTEND_LIB = Path(__file__).resolve().parents[3] / "frontend" / "src" / "lib"
NAV_TABLE = FRONTEND_LIB / "components" / "shell" / "nav.ts"
#: Where the menu table's ``GROUP.*`` names resolve — the frontend's own copy of
#: the group names, held for UI gating (adr-44 rule 8).
GROUP_CONSTANTS = FRONTEND_LIB / "auth.ts"

#: Menu item key → the permission class whose ``read_groups`` it must mirror.
#: ``None`` means the item is not matrix-gated and the frontend must declare it
#: visible to every role (``null``).
ITEM_AREA = {
    "dashboard": None,
    "intake": roles.LivestockAccess,
    "pesajes": roles.LivestockAccess,
    "feeding": roles.FeedExecutionAccess,
    "sanitary": roles.SanitaryAccess,
    "mixer": roles.FeedyardAccess,
    "racion": roles.FeedyardAccess,
    "stocks": roles.FeedDeliveryAccess,
    "ledger": roles.LedgerReadAccess,
    "gastos": roles.ExpensesAccess,
    "clients": roles.ClientDirectoryAccess,
    "advisors": roles.AdvisorAccess,
    "prices": roles.MarketAccess,
}

#: Items gated by something other than a matrix area, with their expected groups.
ITEM_EXPLICIT = {
    # Users & permissions is IsInAdminsGroup, not a GroupMatrixPermission area.
    "users": {ADMINS_GROUP},
}


def parse_group_constants() -> dict[str, str]:
    """``GROUP.FIELD_MANAGERS`` → ``"field_managers"``."""
    source = GROUP_CONSTANTS.read_text(encoding="utf-8")
    body = re.search(r"export const GROUP = \{(.*?)^\} as const;", source, re.S | re.M)
    assert body, f"GROUP constant not found in {GROUP_CONSTANTS}"
    return dict(re.findall(r"([A-Z_]+):\s*\"([a-z_]+)\"", body.group(1)))


def parse_nav_item_groups() -> dict[str, set[str] | None]:
    """Read NAV_ITEM_GROUPS out of the frontend table.

    Deliberately a text parse: running the frontend toolchain from a Django test
    would couple the suites, and the table is a flat literal by design.
    """
    constants = parse_group_constants()
    source = NAV_TABLE.read_text(encoding="utf-8")
    body = re.search(
        r"export const NAV_ITEM_GROUPS[^=]*=\s*\{(.*?)^\};",
        source,
        re.S | re.M,
    )
    assert body, f"NAV_ITEM_GROUPS not found in {NAV_TABLE}"

    parsed: dict[str, set[str] | None] = {}
    for key, value in re.findall(
        r"^\s*([A-Za-z_][\w]*):\s*(null|\[[^\]]*\]),", body.group(1), re.M
    ):
        if value == "null":
            parsed[key] = None
            continue
        names = re.findall(r"GROUP\.([A-Z_]+)|\"([a-z_]+)\"", value)
        resolved = set()
        for constant, literal in names:
            if constant:
                assert constant in constants, f"unknown GROUP.{constant} in {key}"
                resolved.add(constants[constant])
            else:
                resolved.add(literal)
        assert resolved, f"{key} declares an unparseable group list: {value}"
        parsed[key] = resolved
    return parsed


def test_frontend_group_names_match_the_role_groups():
    """The frontend's group-name copy must name the real groups (adr-44 rule 1)."""
    constants = parse_group_constants()
    assert set(constants.values()) == set(roles.ROLE_GROUPS) | {ADMINS_GROUP}


def test_parse_finds_the_whole_table():
    """A parse that silently found nothing would make every assertion vacuous."""
    parsed = parse_nav_item_groups()
    assert set(parsed) == set(ITEM_AREA) | set(ITEM_EXPLICIT), (
        "the frontend menu table and this test's binding disagree on which items "
        "exist; add the new item here with the permission class that governs it"
    )


def test_every_matrix_item_mirrors_its_read_groups():
    parsed = parse_nav_item_groups()
    for item, area in ITEM_AREA.items():
        if area is None:
            assert parsed[item] is None, (
                f"{item} is not matrix-gated, so the menu must declare it null"
            )
            continue
        assert parsed[item] == set(area.read_groups), (
            f"menu item {item!r} declares {sorted(parsed[item] or [])} but "
            f"{area.__name__}.read_groups is {sorted(area.read_groups)} — "
            "update frontend/src/lib/components/shell/nav.ts to match the matrix"
        )


def test_non_matrix_items_declare_their_expected_groups():
    parsed = parse_nav_item_groups()
    for item, expected in ITEM_EXPLICIT.items():
        assert parsed[item] == expected, (
            f"menu item {item!r} declares {sorted(parsed[item] or [])}, expected {sorted(expected)}"
        )


def test_admins_is_never_listed_beside_a_matrix_area():
    """`admins` passes every area already (adr-10); listing it would be noise."""
    parsed = parse_nav_item_groups()
    for item, area in ITEM_AREA.items():
        if area is None:
            continue
        assert ADMINS_GROUP not in (parsed[item] or set()), (
            f"{item} lists {ADMINS_GROUP} explicitly; it is the standing superset"
        )
