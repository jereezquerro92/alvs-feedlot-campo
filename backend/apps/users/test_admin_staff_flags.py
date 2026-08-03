"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

import pytest
from django.test import override_settings

from apps.users.services import upsert_user_from_claims

pytestmark = pytest.mark.django_db


def _login(sub, email):
    return upsert_user_from_claims(
        {"sub": sub, "email": email, "given_name": "Dev", "family_name": "User"}
    )


@override_settings(AUTH_BOOTSTRAP_ALLOWLIST={"admin@example.com": "admins"})
def test_allowlisted_admins_account_gains_staff_and_superuser_access():
    user = _login("sub-admin", "admin@example.com")
    user.refresh_from_db()
    assert user.groups.filter(name="admins").exists()
    assert user.is_staff is True
    assert user.is_superuser is True


@override_settings(AUTH_BOOTSTRAP_ALLOWLIST={"admin@example.com": "admins"})
def test_non_allowlisted_account_stays_off_the_admin_site():
    user = _login("sub-plain", "someone-else@example.com")
    user.refresh_from_db()
    assert not user.groups.exists()
    assert user.is_staff is False
    assert user.is_superuser is False


@override_settings(AUTH_BOOTSTRAP_ALLOWLIST={"admin@example.com": "admins"})
def test_removing_admins_group_membership_revokes_staff_access():
    user = _login("sub-admin-revoke", "admin@example.com")
    user.refresh_from_db()
    assert user.is_staff is True

    from django.contrib.auth.models import Group

    user.groups.remove(Group.objects.get(name="admins"))
    user.refresh_from_db()
    assert user.is_staff is False
    assert user.is_superuser is False
