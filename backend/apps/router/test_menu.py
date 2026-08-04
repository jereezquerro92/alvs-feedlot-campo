"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.router.menu import build_menu
from apps.router.models import ESCALATE, NO_MATCH, Intent
from apps.users.permissions import ADMINS_GROUP

pytestmark = pytest.mark.django_db

User = get_user_model()


def _user(sub="sub-plain"):
    return User.objects.create_user(sub=sub)


def _admin_user(sub="sub-admin"):
    """A user whose ONLY membership is `admins` — never the gate group under
    test, so a row it sees is seen through the superset, not through a gate."""
    user = _user(sub=sub)
    admins, _created = Group.objects.get_or_create(name=ADMINS_GROUP)
    user.groups.add(admins)
    return user


def test_fresh_no_group_user_gets_non_degenerate_menu():
    """#104: a user with zero group memberships and zero visible registry
    intents still gets a valid, non-empty menu (the two reserved outcomes)."""
    Intent.objects.create(phrase="gated", target="/gated/", order=1, group=Group.objects.create(name="gated-group"))
    user = _user()
    menu, by_phrase = build_menu(user)
    assert menu == [
        {"phrase": NO_MATCH, "target": None, "kind": None},
        {"phrase": ESCALATE, "target": None, "kind": None},
    ]
    assert by_phrase == {}


def test_ungated_intent_visible_to_group_less_user():
    Intent.objects.create(phrase="log me out", target="/accounts/logout/", kind="confirm", order=1)
    user = _user()
    menu, by_phrase = build_menu(user)
    phrases = [entry["phrase"] for entry in menu]
    assert "log me out" in phrases
    assert NO_MATCH in phrases
    assert ESCALATE in phrases
    assert by_phrase["log me out"].target == "/accounts/logout/"


def test_gated_intent_hidden_until_group_membership():
    group, _ = Group.objects.get_or_create(name="router-test-group")
    Intent.objects.create(phrase="open the admin site", target="/admin/", order=1, group=group)
    user = _user()

    menu, _by_phrase = build_menu(user)
    assert "open the admin site" not in [e["phrase"] for e in menu]

    user.groups.add(group)
    menu, _by_phrase = build_menu(user)
    assert "open the admin site" in [e["phrase"] for e in menu]


def test_admins_user_sees_every_active_gated_intent():
    """#135: `admins` is the standing app-wide superset (signals.py mirrors it
    into is_staff/is_superuser), so the menu's gate check short-circuits for it
    — every active row is visible, including gates the user does not belong to.
    Still a Django-side authorization decision taken before inference, so the
    router only ever narrows within an already-authorized set
    ([[adr-15-chatbot-two-tier]] rules 2/3)."""
    alpha = Group.objects.create(name="gate-alpha")
    beta = Group.objects.create(name="gate-beta")
    Intent.objects.create(phrase="ungated", target="/ungated/", order=1)
    Intent.objects.create(phrase="alpha only", target="/alpha/", order=2, group=alpha)
    Intent.objects.create(phrase="beta only", target="/beta/", order=3, group=beta)

    user = _admin_user()
    assert set(user.groups.values_list("name", flat=True)) == {ADMINS_GROUP}

    menu, by_phrase = build_menu(user)
    assert [entry["phrase"] for entry in menu] == [
        "ungated",
        "alpha only",
        "beta only",
        NO_MATCH,
        ESCALATE,
    ]
    assert set(by_phrase) == {"ungated", "alpha only", "beta only"}
    assert by_phrase["beta only"].target == "/beta/"


def test_role_less_user_unaffected_by_admins_superset():
    """The superset widens `admins` only: a user with zero memberships keeps
    seeing exactly the ungated rows plus the two reserved outcomes."""
    gamma = Group.objects.create(name="gate-gamma")
    Intent.objects.create(phrase="ungated", target="/ungated/", order=1)
    Intent.objects.create(phrase="gamma only", target="/gamma/", order=2, group=gamma)

    user = _user(sub="sub-role-less")
    menu, by_phrase = build_menu(user)
    assert [entry["phrase"] for entry in menu] == ["ungated", NO_MATCH, ESCALATE]
    assert set(by_phrase) == {"ungated"}


def test_menu_ordering_is_explicit_and_deterministic():
    """#94: ordering follows Intent.order, not insertion or Meta.ordering
    alone; NO_MATCH always precedes ESCALATE."""
    Intent.objects.create(phrase="second", target="/second/", order=2)
    Intent.objects.create(phrase="first", target="/first/", order=1)
    user = _user()

    menu, _by_phrase = build_menu(user)
    phrases = [entry["phrase"] for entry in menu]
    assert phrases == ["first", "second", NO_MATCH, ESCALATE]


def test_inactive_intent_excluded():
    Intent.objects.create(phrase="disabled", target="/disabled/", order=1, is_active=False)
    user = _user()
    menu, _by_phrase = build_menu(user)
    assert "disabled" not in [e["phrase"] for e in menu]


def test_inactive_intent_hidden_even_from_admins_user():
    """`is_active` is a registry-state filter, not a permission one, so the
    superset does not reach past it: a retired row stays invisible to `admins`
    and the menu falls back to the two reserved outcomes."""
    delta = Group.objects.create(name="gate-delta")
    Intent.objects.create(
        phrase="retired gated", target="/retired-gated/", order=1, group=delta, is_active=False
    )
    Intent.objects.create(
        phrase="retired ungated", target="/retired-ungated/", order=2, is_active=False
    )

    user = _admin_user(sub="sub-admin-inactive")
    menu, by_phrase = build_menu(user)
    assert [entry["phrase"] for entry in menu] == [NO_MATCH, ESCALATE]
    assert by_phrase == {}


def test_phrase_collision_rejected_at_write_time():
    """SECURITY #266: the phrase collision that could resolve `by_phrase` to a
    gated row is now structurally impossible — `Intent.phrase` is unique, so a
    second row sharing a phrase is rejected DB-side at data-entry time instead
    of silently first-winning at read time ([[adr-15-chatbot-two-tier]] rule 2)."""
    gated_group, _ = Group.objects.get_or_create(name="collision-gated-group")
    Intent.objects.create(phrase="log out", target="/accounts/logout/", order=1)
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            Intent.objects.create(
                phrase="log out", target="/admin/secret-panel/", order=2, group=gated_group
            )


@pytest.mark.parametrize("reserved", [NO_MATCH, ESCALATE])
def test_reserved_outcome_phrase_rejected(reserved):
    """An `Intent.phrase` equal to a reserved outcome is rejected both by the
    admin-surfacing validation path (`full_clean`) and DB-side, so `by_phrase`
    can never hold a reserved-outcome key ([[adr-15-chatbot-two-tier]] rule 2)."""
    with pytest.raises(ValidationError):
        Intent(phrase=reserved, target="/x/").full_clean()

    with transaction.atomic():
        with pytest.raises(IntegrityError):
            Intent.objects.create(phrase=reserved, target="/x/")


def test_by_phrase_never_contains_reserved_key():
    """With the reserved-outcome constraint in place, no registry row can carry
    a reserved phrase, so `by_phrase` never collides with NO_MATCH/ESCALATE —
    the pre-`NO_MATCH`-check lookup in views.py can never attach a wrong
    `chosen_intent` to a reserved-outcome audit row."""
    Intent.objects.create(phrase="log me out", target="/accounts/logout/", order=1)
    user = _user()
    _menu, by_phrase = build_menu(user)
    assert set(by_phrase) & {NO_MATCH, ESCALATE} == set()
