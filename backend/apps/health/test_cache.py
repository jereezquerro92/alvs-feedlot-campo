"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

from importlib import reload

import pytest
from django.conf import settings
from django.core.cache import caches
from django.core.management import call_command
from django.db import connection
from django.urls import clear_url_caches

from apps.users import oidc

MODEL_BACKEND = "django.contrib.auth.backends.ModelBackend"


def test_default_cache_is_database_cache():
    default = settings.CACHES["default"]
    assert default["BACKEND"] == "django.core.cache.backends.db.DatabaseCache"
    assert default["LOCATION"] == "django_cache_table"


def test_locmem_secondary_alias_exists():
    backends = {name: cfg["BACKEND"] for name, cfg in settings.CACHES.items()}
    assert (
        "django.core.cache.backends.locmem.LocMemCache" in backends.values()
    ), "a LocMemCache secondary alias must exist"
    assert (
        backends["default"] != "django.core.cache.backends.locmem.LocMemCache"
    ), "LocMemCache is a secondary alias, never the default"


def test_no_cache_server_configured():
    forbidden = ("redis", "elasticache", "memcached", "pymemcache")
    for cfg in settings.CACHES.values():
        backend = cfg["BACKEND"].lower()
        assert not any(f in backend for f in forbidden), backend


def test_database_cache_options_bounded():
    options = settings.CACHES["default"].get("OPTIONS", {})
    assert "MAX_ENTRIES" in options, "the DB cache table must be bounded"
    assert "CULL_FREQUENCY" in options


@pytest.mark.django_db
def test_createcachetable_creates_table():
    call_command("createcachetable")
    assert "django_cache_table" in connection.introspection.table_names()


@pytest.mark.django_db
def test_database_cache_roundtrip():
    call_command("createcachetable")
    cache = caches["default"]
    cache.set("tdd05-key", "tdd05-value", timeout=30)
    assert cache.get("tdd05-key") == "tdd05-value"


def _admin_user(django_user_model):
    from django.contrib.auth.models import Group

    user = django_user_model.objects.create(sub="cache-admin", email="a@example.com")
    user.groups.add(Group.objects.get(name="admins"))
    return user


@pytest.mark.django_db
def test_every_declared_endpoint_sets_cache_control(client, settings, monkeypatch, django_user_model):
    settings.COGNITO_DOMAIN = "https://auth.example.com"
    settings.COGNITO_CLIENT_ID = "client-123"
    monkeypatch.setattr(oidc, "exchange_code", lambda code, redirect_uri: {"id_token": "mock"})
    monkeypatch.setattr(
        oidc,
        "verify_id_token",
        lambda id_token: {"sub": "s", "email": "e@example.com", "given_name": "G", "family_name": "F"},
    )

    always = [
        client.get("/api/health/"),
        client.get("/accounts/login/"),
        client.post("/accounts/logout/"),
        client.get("/accounts/callback/"),
    ]
    for response in always:
        assert response.has_header("Cache-Control"), response

    user = _admin_user(django_user_model)
    client.force_login(user, backend=MODEL_BACKEND)
    for path in ("/api/me/", "/api/restricted/"):
        response = client.get(path)
        assert response.has_header("Cache-Control"), path


@pytest.mark.django_db
def test_django_native_non_2xx_responses_carry_cache_control(client):
    from django.test import Client

    csrf_client = Client(enforce_csrf_checks=True)
    csrf_response = csrf_client.post("/accounts/logout/")
    assert csrf_response.status_code == 403, csrf_response.status_code

    append_slash_response = client.get("/api/health")
    assert append_slash_response.status_code == 301, append_slash_response.status_code

    responses = {
        "CSRF-403 (POST /accounts/logout/ without token)": csrf_response,
        "APPEND_SLASH 301 (GET /api/health)": append_slash_response,
    }
    for label, response in responses.items():
        assert response.has_header("Cache-Control"), label
        assert response["Cache-Control"] == "no-store", label


@pytest.mark.django_db
def test_dev_login_sets_cache_control(client, settings, django_user_model):
    import apps.users.urls as users_urls
    import config.urls as root_urls

    settings.DEBUG = True
    settings.AUTH_DEV_MODE = True
    reload(users_urls)
    reload(root_urls)
    clear_url_caches()
    try:
        response = client.get("/accounts/dev-login/")
        assert response.status_code in (200, 302)
        assert response["Cache-Control"] == "no-store"
    finally:
        settings.DEBUG = False
        reload(users_urls)
        reload(root_urls)
        clear_url_caches()


@pytest.mark.django_db
def test_non_2xx_responses_also_carry_cache_control(client):
    responses = {
        "anonymous GET /api/me/ (403)": client.get("/api/me/"),
        "GET on an undeclared route (404)": client.get("/no/such/route/"),
        "GET on POST-only /accounts/logout/ (405)": client.get("/accounts/logout/"),
    }
    for label, response in responses.items():
        assert response.has_header("Cache-Control"), label
        assert response["Cache-Control"] == "no-store", label


@pytest.mark.django_db
def test_authenticated_responses_are_no_store(client, django_user_model):
    user = _admin_user(django_user_model)
    client.force_login(user, backend=MODEL_BACKEND)
    for path in ("/api/me/", "/api/restricted/"):
        assert client.get(path)["Cache-Control"] == "no-store", path


@pytest.mark.django_db
def test_public_response_also_explicit(client):
    assert client.get("/api/health/")["Cache-Control"] == "no-store"
