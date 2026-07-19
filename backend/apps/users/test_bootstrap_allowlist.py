"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

import pytest
from django.contrib.auth.models import Group
from django.test import override_settings

from apps.users.models import AccessRequest
from apps.users.services import upsert_user_from_claims
from config.settings import _env_allowlist

pytestmark = pytest.mark.django_db

CLAIMS = {
    "sub": "sub-allowlist",
    "email": "dev@example.com",
    "given_name": "Dev",
    "family_name": "User",
}


def _login(sub="sub-allowlist", **overrides):
    data = {**CLAIMS, **overrides, "sub": sub}
    return upsert_user_from_claims(data)


@override_settings(AUTH_BOOTSTRAP_ALLOWLIST={"dev@example.com": "admins"})
def test_allowlisted_email_gets_role_and_group_on_first_login():
    user = _login()
    access_request = AccessRequest.objects.get(user=user)
    assert access_request.role == Group.objects.get(name="admins")
    assert user.groups.filter(name="admins").exists()


@override_settings(AUTH_BOOTSTRAP_ALLOWLIST={"dev@example.com": "admins"})
def test_non_allowlisted_email_stays_pending():
    user = _login(sub="sub-other", email="other@example.com")
    assert AccessRequest.objects.get(user=user).role is None
    assert user.groups.count() == 0


def test_empty_allowlist_preserves_current_behavior():
    user = _login(sub="sub-empty")
    assert AccessRequest.objects.get(user=user).role is None
    assert user.groups.count() == 0


@override_settings(AUTH_BOOTSTRAP_ALLOWLIST={"dev@example.com": "admins"})
def test_grant_is_idempotent_across_logins():
    _login()
    user = _login()
    assert AccessRequest.objects.filter(user=user).count() == 1
    assert list(user.groups.values_list("name", flat=True)) == ["admins"]


def test_allowlist_entry_added_later_grants_on_next_login():
    user = _login(sub="sub-late")
    assert AccessRequest.objects.get(user=user).role is None
    with override_settings(AUTH_BOOTSTRAP_ALLOWLIST={"dev@example.com": "ai_operators"}):
        user = _login(sub="sub-late")
    assert user.groups.filter(name="ai_operators").exists()


@override_settings(AUTH_BOOTSTRAP_ALLOWLIST={"dev@example.com": "ai_operators"})
def test_allowlist_does_not_override_admin_set_role():
    user = _login(sub="sub-admin-first")
    access_request = AccessRequest.objects.get(user=user)
    access_request.role = Group.objects.get(name="admins")
    access_request.save()
    user = _login(sub="sub-admin-first")
    access_request.refresh_from_db()
    assert access_request.role == Group.objects.get(name="admins")


@override_settings(AUTH_BOOTSTRAP_ALLOWLIST={"dev@example.com": "no-such-group"})
def test_unknown_group_is_skipped_and_login_still_works():
    user = _login(sub="sub-typo")
    assert AccessRequest.objects.get(user=user).role is None
    assert not Group.objects.filter(name="no-such-group").exists()


@override_settings(AUTH_BOOTSTRAP_ALLOWLIST={"dev@example.com": "admins"})
def test_email_match_is_case_insensitive():
    user = _login(sub="sub-case", email="Dev@Example.COM")
    assert user.groups.filter(name="admins").exists()


def test_env_allowlist_parses_pairs_defaults_and_whitespace(monkeypatch):
    monkeypatch.setenv(
        "AUTH_BOOTSTRAP_ALLOWLIST",
        " Dev@Example.com : admins , owner@corp.com ,, bad-entry:ai_operators ",
    )
    assert _env_allowlist("AUTH_BOOTSTRAP_ALLOWLIST") == {
        "dev@example.com": "admins",
        "owner@corp.com": "admins",
        "bad-entry": "ai_operators",
    }


def test_env_allowlist_unset_is_empty(monkeypatch):
    monkeypatch.delenv("AUTH_BOOTSTRAP_ALLOWLIST", raising=False)
    assert _env_allowlist("AUTH_BOOTSTRAP_ALLOWLIST") == {}
