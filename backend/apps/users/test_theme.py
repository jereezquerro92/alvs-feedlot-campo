"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

import importlib
import json
from urllib.parse import unquote

import pytest

import apps.users.urls
import config.urls
from apps.users import oidc
from apps.users.models import User
from apps.users.services import upsert_user_from_claims
from django.urls import clear_url_caches

pytestmark = pytest.mark.django_db

ME = "/api/me/"
CLAIMS = {
    "sub": "sub-theme",
    "email": "theme@example.com",
    "given_name": "Theme",
    "family_name": "User",
}

VALID_THEME = {
    "mode": "dark",
    "bgPreset": "melt",
    "colors": {
        "background": "#101010",
        "primary": "oklch(0.6 0.2 250)",
        "secondary": "rgb(10, 20, 30)",
        "accent": "hsl(200, 50%, 50%)",
    },
    "radius": "0.625rem",
}


def _user(sub="sub-theme", **overrides):
    data = {**CLAIMS, **overrides, "sub": sub}
    return upsert_user_from_claims(data)


def _decoded_theme_cookie(response):
    cookie = response.cookies.get("theme")
    assert cookie is not None, "expected a `theme` Set-Cookie on the response"
    return json.loads(unquote(cookie.value))


# --- GET --------------------------------------------------------------------


def test_me_get_includes_theme_config_default_empty(client):
    user = _user()
    client.force_login(user)
    assert client.get(ME).json()["theme_config"] == {}


def test_me_get_returns_persisted_theme_config(client):
    user = _user(sub="sub-theme-get")
    user.theme_config = VALID_THEME
    user.save()
    client.force_login(user)
    assert client.get(ME).json()["theme_config"] == VALID_THEME


# --- PATCH happy path ---------------------------------------------------


def test_me_patch_valid_theme_config_persists_and_sets_theme_cookie(client, settings):
    settings.CSRF_COOKIE_SECURE = True
    user = _user(sub="sub-theme-valid")
    client.force_login(user)
    response = client.patch(ME, {"theme_config": VALID_THEME}, content_type="application/json")

    assert response.status_code == 200
    assert response.json()["theme_config"] == VALID_THEME
    user.refresh_from_db()
    assert user.theme_config == VALID_THEME

    assert _decoded_theme_cookie(response) == VALID_THEME
    cookie = response.cookies["theme"]
    assert cookie["path"] == "/"
    assert cookie["samesite"] == "Lax"
    assert int(cookie["max-age"]) == 31536000
    assert not cookie["httponly"]
    assert cookie["secure"]


def test_me_patch_theme_config_replaces_wholesale(client):
    user = _user(sub="sub-theme-replace")
    user.theme_config = {
        "mode": "dark",
        "bgPreset": "melt",
        "colors": {"background": "#000000"},
        "radius": "1rem",
    }
    user.save()
    client.force_login(user)
    response = client.patch(ME, {"theme_config": {"mode": "light"}}, content_type="application/json")
    assert response.status_code == 200
    assert response.json()["theme_config"] == {"mode": "light"}
    user.refresh_from_db()
    assert user.theme_config == {"mode": "light"}


def test_me_patch_without_theme_config_key_leaves_blob_and_cookie_unchanged(client):
    user = _user(sub="sub-theme-untouched")
    user.theme_config = VALID_THEME
    user.save()
    client.force_login(user)
    response = client.patch(ME, {"nickname": "Ada"}, content_type="application/json")
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.theme_config == VALID_THEME
    assert "theme" not in response.cookies


# --- PATCH rejection ------------------------------------------------------


def test_me_patch_theme_config_unknown_top_level_key_rejected(client):
    user = _user(sub="sub-theme-unknown-key")
    client.force_login(user)
    response = client.patch(
        ME, {"theme_config": {"mode": "dark", "wat": "nope"}}, content_type="application/json"
    )
    assert response.status_code == 400
    user.refresh_from_db()
    assert user.theme_config == {}
    assert "theme" not in response.cookies


def test_me_patch_theme_config_unknown_color_key_rejected(client):
    user = _user(sub="sub-theme-unknown-color")
    client.force_login(user)
    response = client.patch(
        ME,
        {"theme_config": {"colors": {"background": "#fff", "border": "#000"}}},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_me_patch_theme_config_bad_mode_enum_rejected(client):
    user = _user(sub="sub-theme-mode")
    client.force_login(user)
    response = client.patch(ME, {"theme_config": {"mode": "blue"}}, content_type="application/json")
    assert response.status_code == 400


def test_me_patch_theme_config_bad_bgpreset_enum_rejected(client):
    user = _user(sub="sub-theme-preset")
    client.force_login(user)
    response = client.patch(
        ME, {"theme_config": {"bgPreset": "wallpaper"}}, content_type="application/json"
    )
    assert response.status_code == 400


@pytest.mark.parametrize(
    "bad_color",
    [
        "red",
        "#fff; background-image: url(evil)",
        "<script>alert(1)</script>",
        'oklch(0 0 0)" onmouseover="alert(1)',
    ],
)
def test_me_patch_theme_config_injection_color_rejected(client, bad_color):
    user = _user(sub="sub-theme-injection")
    client.force_login(user)
    response = client.patch(
        ME,
        {"theme_config": {"colors": {"background": bad_color}}},
        content_type="application/json",
    )
    assert response.status_code == 400
    user.refresh_from_db()
    assert user.theme_config == {}


@pytest.mark.parametrize(
    "good_color",
    [
        "#fff",
        "rgb(10, 20, 30)",
        "rgba(10, 20, 30, 0.5)",
        "hsl(200, 50%, 50%)",
        "oklch(0.6 0.2 250)",
    ],
)
def test_me_patch_theme_config_accepts_all_color_forms(client, good_color):
    user = _user(sub="sub-theme-good-color")
    client.force_login(user)
    response = client.patch(
        ME,
        {"theme_config": {"colors": {"background": good_color}}},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["theme_config"]["colors"]["background"] == good_color


@pytest.mark.parametrize("bad_radius", [12, "10px;evil", "url(x)"])
def test_me_patch_theme_config_bad_radius_rejected(client, bad_radius):
    user = _user(sub="sub-theme-radius")
    user.theme_config = VALID_THEME
    user.save()
    client.force_login(user)
    response = client.patch(
        ME, {"theme_config": {"radius": bad_radius}}, content_type="application/json"
    )
    assert response.status_code == 400
    user.refresh_from_db()
    assert user.theme_config == VALID_THEME


def test_me_patch_theme_config_not_object_rejected(client):
    user = _user(sub="sub-theme-not-object")
    client.force_login(user)
    response = client.patch(ME, {"theme_config": "dark"}, content_type="application/json")
    assert response.status_code == 400


def test_me_patch_theme_config_no_store(client):
    user = _user(sub="sub-theme-no-store")
    client.force_login(user)
    response = client.patch(ME, {"theme_config": VALID_THEME}, content_type="application/json")
    assert response["Cache-Control"] == "no-store"


# --- login views mirror theme_config into the `theme` cookie ---------------


def _prime_state(client, state="state-xyz"):
    session = client.session
    session[oidc.STATE_SESSION_KEY] = state
    session.save()
    return state


def _mock_ok(monkeypatch, claims):
    monkeypatch.setattr(oidc, "exchange_code", lambda code, redirect_uri: {"id_token": "mock"})
    monkeypatch.setattr(oidc, "verify_id_token", lambda id_token: dict(claims))


def test_callback_sets_theme_cookie_from_existing_user(client, monkeypatch):
    sub = "sub-theme-callback"
    claims = {**CLAIMS, "sub": sub}
    User.objects.create(sub=sub, email=claims["email"], theme_config=VALID_THEME)
    _mock_ok(monkeypatch, claims)
    state = _prime_state(client)
    response = client.get(f"/accounts/callback/?code=abc&state={state}")
    assert response.status_code == 302
    assert _decoded_theme_cookie(response) == VALID_THEME


def test_dev_login_sets_theme_cookie(client, settings):
    settings.DEBUG = True
    settings.AUTH_DEV_MODE = True
    settings.AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
        "apps.users.backends.DevLoginBackend",
    ]
    clear_url_caches()
    importlib.reload(apps.users.urls)
    importlib.reload(config.urls)
    try:
        User.objects.create(
            sub="dev-theme@example.com", email="theme@example.com", theme_config=VALID_THEME
        )
        response = client.get("/accounts/dev-login/?email=theme@example.com")
        assert response.status_code == 302
        assert _decoded_theme_cookie(response) == VALID_THEME
    finally:
        settings.DEBUG = False
        settings.AUTH_DEV_MODE = False
        clear_url_caches()
        importlib.reload(apps.users.urls)
        importlib.reload(config.urls)
