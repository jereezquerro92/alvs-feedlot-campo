"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.test import RequestFactory

from apps.users.admin import ROLE_HELP_TEXT, AccessRequestAdmin
from apps.users.models import AccessRequest
from apps.users.services import upsert_user_from_claims

pytestmark = pytest.mark.django_db

ME = "/api/me/"
CLAIMS = {
    "sub": "sub-lobby",
    "email": "lobby@example.com",
    "given_name": "Lobby",
    "family_name": "User",
}


def _user(sub="sub-lobby", **overrides):
    data = {**CLAIMS, **overrides, "sub": sub}
    return upsert_user_from_claims(data)


def _admins():
    return Group.objects.get(name="admins")


def _ai_operators():
    return Group.objects.get(name="ai_operators")


def test_first_login_creates_exactly_one_access_request():
    user = _user()
    assert AccessRequest.objects.filter(user=user).count() == 1


def test_access_request_role_is_null_by_default():
    user = _user()
    access_request = AccessRequest.objects.get(user=user)
    assert access_request.role is None


def test_second_login_creates_no_duplicate():
    _user()
    _user()
    assert AccessRequest.objects.filter(user__sub="sub-lobby").count() == 1


def test_setting_role_adds_group_to_user():
    user = _user(sub="sub-role-assign")
    access_request = AccessRequest.objects.get(user=user)
    access_request.role = _admins()
    access_request.save()
    user.refresh_from_db()
    assert user.groups.filter(name="admins").exists()


def test_resave_same_role_is_idempotent():
    user = _user(sub="sub-role-resave")
    access_request = AccessRequest.objects.get(user=user)
    access_request.role = _ai_operators()
    access_request.save()
    access_request.role = _ai_operators()
    access_request.save()
    user.refresh_from_db()
    assert list(user.groups.filter(name="ai_operators")) == [_ai_operators()]


def test_resave_null_role_does_not_error():
    user = _user(sub="sub-role-null")
    access_request = AccessRequest.objects.get(user=user)
    access_request.save()
    assert user.groups.count() == 0


def _model_admin():
    return AccessRequestAdmin(AccessRequest, AdminSite())


def _request():
    return RequestFactory().get("/admin/users/accessrequest/")


def test_admin_role_editable_while_pending():
    user = _user(sub="sub-admin-pending")
    access_request = AccessRequest.objects.get(user=user)
    assert "role" not in _model_admin().get_readonly_fields(_request(), access_request)


def test_admin_role_readonly_after_grant():
    user = _user(sub="sub-admin-granted")
    access_request = AccessRequest.objects.get(user=user)
    access_request.role = _admins()
    access_request.save()
    assert "role" in _model_admin().get_readonly_fields(_request(), access_request)


def test_admin_role_help_text_documents_grant_only_contract():
    form = _model_admin().get_form(_request(), None)
    assert form.base_fields["role"].help_text == ROLE_HELP_TEXT


def test_reassign_role_adds_new_group_and_keeps_old():
    user = _user(sub="sub-role-reassign")
    access_request = AccessRequest.objects.get(user=user)
    access_request.role = _admins()
    access_request.save()
    access_request.role = _ai_operators()
    access_request.save()
    user.refresh_from_db()
    assert user.groups.filter(name="admins").exists()
    assert user.groups.filter(name="ai_operators").exists()


def test_clearing_role_does_not_remove_group():
    user = _user(sub="sub-role-clear")
    access_request = AccessRequest.objects.get(user=user)
    access_request.role = _admins()
    access_request.save()
    access_request.role = None
    access_request.save()
    user.refresh_from_db()
    assert user.groups.filter(name="admins").exists()


def test_me_endpoint_does_not_leak_access_request(client):
    user = _user(sub="sub-me-shape")
    client.force_login(user)
    response = client.get(ME)
    assert response.status_code == 200
    assert response.json() == {
        "sub": user.sub,
        "email": user.email,
        "given_name": user.given_name,
        "family_name": user.family_name,
        "picture": "",
        "groups": [],
        "nickname": "",
        "avatar_visible": True,
        "theme_config": {},
    }
    assert "access_request" not in response.json()
    assert "role" not in response.json()
