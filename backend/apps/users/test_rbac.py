"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

import pytest
from django.contrib.auth.models import Group

from apps.users.services import upsert_user_from_claims

pytestmark = pytest.mark.django_db

ME = "/api/me/"
RESTRICTED = "/api/restricted/"
CLAIMS = {
    "sub": "sub-plain",
    "email": "plain@example.com",
    "given_name": "Plain",
    "family_name": "User",
}


def _user(sub="sub-plain", **overrides):
    data = {**CLAIMS, **overrides, "sub": sub}
    return upsert_user_from_claims(data)


def _admins():
    return Group.objects.get(name="admins")


def test_admins_group_exists():
    assert Group.objects.filter(name="admins").exists()


def test_me_requires_session(client):
    response = client.get(ME)
    assert response.status_code in (401, 403)
    assert "sub" not in response.json()


def test_me_returns_current_user(client):
    user = _user()
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


def test_me_mirrors_picture_claim(client):
    user = _user(sub="sub-picture", picture="https://example.com/avatar.jpg")
    client.force_login(user)
    assert client.get(ME).json()["picture"] == "https://example.com/avatar.jpg"


def test_me_picture_defaults_empty_when_claim_absent(client):
    user = _user()
    client.force_login(user)
    assert client.get(ME).json()["picture"] == ""


def test_me_groups_are_django_group_names(client):
    user = _user()
    user.groups.add(_admins())
    client.force_login(user)
    assert client.get(ME).json()["groups"] == ["admins"]


def test_me_no_store(client):
    client.force_login(_user())
    assert client.get(ME)["Cache-Control"] == "no-store"


def test_me_patch_updates_nickname(client):
    user = _user(sub="sub-patch-nickname")
    client.force_login(user)
    response = client.patch(ME, {"nickname": "Ada"}, content_type="application/json")
    assert response.status_code == 200
    assert response.json()["nickname"] == "Ada"
    user.refresh_from_db()
    assert user.nickname == "Ada"


def test_me_patch_updates_avatar_visible(client):
    user = _user(sub="sub-patch-avatar")
    client.force_login(user)
    response = client.patch(ME, {"avatar_visible": False}, content_type="application/json")
    assert response.status_code == 200
    assert response.json()["avatar_visible"] is False
    user.refresh_from_db()
    assert user.avatar_visible is False


def test_me_patch_rejects_mismatched_read_only_field(client):
    user = _user(sub="sub-patch-readonly")
    client.force_login(user)
    response = client.patch(ME, {"email": "other@example.com"}, content_type="application/json")
    assert response.status_code == 400


def test_me_patch_allows_read_only_field_matching_current_value(client):
    user = _user(sub="sub-patch-readonly-match")
    client.force_login(user)
    response = client.patch(ME, {"email": user.email}, content_type="application/json")
    assert response.status_code == 200


def test_me_patch_allows_blank_nickname(client):
    user = _user(sub="sub-patch-blank")
    user.nickname = "Old"
    user.save()
    client.force_login(user)
    response = client.patch(ME, {"nickname": ""}, content_type="application/json")
    assert response.status_code == 200
    assert response.json()["nickname"] == ""


def test_me_patch_requires_session(client):
    response = client.patch(ME, {"nickname": "Ada"}, content_type="application/json")
    assert response.status_code in (401, 403)


def test_me_patch_no_store(client):
    client.force_login(_user(sub="sub-patch-no-store"))
    response = client.patch(ME, {"nickname": "Ada"}, content_type="application/json")
    assert response["Cache-Control"] == "no-store"


def test_restricted_200_for_admins_member(client):
    user = _user(sub="sub-admin")
    user.groups.add(_admins())
    client.force_login(user)
    response = client.get(RESTRICTED)
    assert response.status_code == 200
    assert response.json() == {"detail": "ok"}


def test_restricted_403_for_non_member(client):
    client.force_login(_user())
    assert client.get(RESTRICTED).status_code == 403


def test_restricted_requires_session(client):
    assert client.get(RESTRICTED).status_code in (401, 403)


def test_restricted_no_store(client):
    user = _user(sub="sub-admin")
    user.groups.add(_admins())
    client.force_login(user)
    assert client.get(RESTRICTED)["Cache-Control"] == "no-store"


def test_permission_reads_only_django_groups(client):
    hostile = {**CLAIMS, "sub": "sub-hostile", "cognito:groups": ["admins"]}
    user = upsert_user_from_claims(hostile)
    assert user.groups.count() == 0
    client.force_login(user)
    assert client.get(RESTRICTED).status_code == 403


def test_group_membership_toggles_access(client):
    user = _user(sub="sub-toggle")
    client.force_login(user)
    assert client.get(RESTRICTED).status_code == 403
    user.groups.add(_admins())
    assert client.get(RESTRICTED).status_code == 200
