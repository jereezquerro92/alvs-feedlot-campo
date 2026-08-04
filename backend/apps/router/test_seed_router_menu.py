"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command

from apps.router.management.commands.seed_router_menu import STARTER_MENU
from apps.router.menu import build_menu
from apps.router.models import ESCALATE, NO_MATCH, Intent, path_relative_validator
from apps.users.roles import FEED_OPERATORS, FIELD_MANAGERS, LOT_OWNERS

pytestmark = pytest.mark.django_db

User = get_user_model()

LOGOUT_PHRASE = "Cerrar sesión"
PROFILE_PHRASE = "Ir al perfil"
CLIENTS_PHRASE = "Abrir clientes"


def _user(sub, group_name=None):
    user = User.objects.create_user(sub=sub)
    if group_name:
        user.groups.add(Group.objects.get(name=group_name))
    return user


def _offered(user):
    menu, _by_phrase = build_menu(user)
    return [entry["phrase"] for entry in menu]


def test_seed_creates_every_starter_row():
    call_command("seed_router_menu")

    rows = {row.phrase: row for row in Intent.objects.all()}
    assert len(rows) == len(STARTER_MENU) == 13
    for phrase, target, kind, group_name, order in STARTER_MENU:
        row = rows[phrase]
        assert row.target == target
        assert row.kind == kind
        assert row.order == order
        assert row.is_active is True
        assert (row.group.name if row.group else None) == group_name


def test_seed_is_idempotent():
    call_command("seed_router_menu")
    call_command("seed_router_menu")

    assert Intent.objects.count() == len(STARTER_MENU)
    phrases = list(Intent.objects.values_list("phrase", flat=True))
    assert len(phrases) == len(set(phrases))


def test_seed_repairs_drifted_row():
    """A re-run restores the fields the product owns: where a phrase points,
    how reversible it is, its order, and who may see it."""
    call_command("seed_router_menu")
    drifted = Intent.objects.get(phrase=PROFILE_PHRASE)
    stray_group = Group.objects.create(name="stray-group")
    Intent.objects.filter(pk=drifted.pk).update(
        target="/elsewhere/", kind="confirm", order=999, group=stray_group
    )

    call_command("seed_router_menu")

    drifted.refresh_from_db()
    assert drifted.target == "/profile/"
    assert drifted.kind == "navigate"
    assert drifted.order == 10
    assert drifted.group.name == FIELD_MANAGERS


def test_deactivated_row_stays_deactivated():
    """`is_active` is the operator's field: a row switched off in /admin/ is
    never resurrected by a re-run (`is_active` absent from `defaults`)."""
    call_command("seed_router_menu")
    Intent.objects.filter(phrase=CLIENTS_PHRASE).update(is_active=False)

    call_command("seed_router_menu")

    assert Intent.objects.get(phrase=CLIENTS_PHRASE).is_active is False


def test_owner_authored_row_survives_the_seed():
    """The seed upserts its own rows; it never synchronises the registry, so a
    hand-authored Intent outside STARTER_MENU is left exactly as it was."""
    owner_row = Intent.objects.create(
        phrase="Ver el tablero del dueño", target="/owner/", kind="navigate", order=500
    )

    call_command("seed_router_menu")

    owner_row.refresh_from_db()
    assert owner_row.target == "/owner/"
    assert owner_row.order == 500
    assert owner_row.is_active is True
    assert Intent.objects.count() == len(STARTER_MENU) + 1


def test_every_target_is_path_relative_and_no_phrase_is_reserved():
    """No starter row can point off-site (#107 path-relative validator) or
    collide with a reserved outcome ([[adr-15-chatbot-two-tier]] rule 2)."""
    call_command("seed_router_menu")

    for row in Intent.objects.all():
        path_relative_validator(row.target)
        assert row.phrase not in (NO_MATCH, ESCALATE)


def test_role_less_session_is_offered_only_logout():
    """adr-20 rules 1-2: a role-less session is confined to the lobby, and the
    only starter destination outside that gate is `/accounts/*`."""
    call_command("seed_router_menu")

    phrases = _offered(_user("sub-role-less"))

    assert phrases == [LOGOUT_PHRASE, NO_MATCH, ESCALATE]
    assert PROFILE_PHRASE not in phrases
    assert CLIENTS_PHRASE not in phrases


def test_field_managers_session_is_offered_every_row():
    call_command("seed_router_menu")

    phrases = _offered(_user("sub-field-manager", FIELD_MANAGERS))

    assert len(phrases) == len(STARTER_MENU) + 2
    for phrase, *_rest in STARTER_MENU:
        assert phrase in phrases
    assert phrases[-2:] == [NO_MATCH, ESCALATE]


def test_lot_owners_session_is_offered_only_logout():
    call_command("seed_router_menu")

    assert _offered(_user("sub-lot-owner", LOT_OWNERS)) == [LOGOUT_PHRASE, NO_MATCH, ESCALATE]


def test_feed_operators_session_is_offered_only_logout():
    """A gate this seed did not grant is a gate that stays shut."""
    call_command("seed_router_menu")

    assert _offered(_user("sub-feed-operator", FEED_OPERATORS)) == [
        LOGOUT_PHRASE,
        NO_MATCH,
        ESCALATE,
    ]


def test_seed_runs_outside_debug(settings):
    """No DEBUG gate: prod needs the same starter menu as local (#135)."""
    settings.DEBUG = False

    call_command("seed_router_menu")

    assert Intent.objects.filter(is_active=True).count() == len(STARTER_MENU)
