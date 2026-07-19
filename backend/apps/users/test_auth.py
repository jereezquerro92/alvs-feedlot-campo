"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

import importlib
import urllib.request
from urllib.parse import parse_qs, urlparse

import pytest
from django.core.checks import Error
from django.core.management import call_command
from django.core.management.base import SystemCheckError
from django.urls import NoReverseMatch, clear_url_caches, reverse

import apps.users.urls
import config.urls
from apps.users import checks, oidc
from apps.users.models import User

SUB = "cognito-sub-123"
CLAIMS = {
    "sub": SUB,
    "email": "ada@example.com",
    "given_name": "Ada",
    "family_name": "Lovelace",
}


def _prime_state(client, state="state-xyz"):
    session = client.session
    session[oidc.STATE_SESSION_KEY] = state
    session.save()
    return state


def _mock_ok(monkeypatch, claims=CLAIMS):
    monkeypatch.setattr(oidc, "exchange_code", lambda code, redirect_uri: {"id_token": "mock"})
    monkeypatch.setattr(oidc, "verify_id_token", lambda id_token: dict(claims))


def test_exchange_code_bounds_urlopen_with_timeout(monkeypatch, settings):
    settings.COGNITO_DOMAIN = "https://auth.example.com"
    settings.COGNITO_CLIENT_ID = "client-123"
    settings.COGNITO_CLIENT_SECRET = "secret-456"

    captured = {}

    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def read(self):
            return b'{"id_token": "mock"}'

    def _fake_urlopen(request, timeout=None):
        captured["request"] = request
        captured["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    result = oidc.exchange_code("code-abc", "http://testserver/accounts/callback/")

    assert result == {"id_token": "mock"}
    assert captured["timeout"] == oidc.TOKEN_EXCHANGE_TIMEOUT_SECONDS
    assert oidc.TOKEN_EXCHANGE_TIMEOUT_SECONDS > 0


@pytest.mark.django_db
def test_login_redirects_to_cognito_authorize(client, settings):
    settings.COGNITO_DOMAIN = "https://auth.example.com"
    settings.COGNITO_CLIENT_ID = "client-123"
    settings.COGNITO_USER_POOL_ID = "pool-789"
    response = client.get("/accounts/login/")
    assert response.status_code == 302
    location = response["Location"]
    assert location.startswith("https://auth.example.com/oauth2/authorize")
    query = parse_qs(urlparse(location).query)
    assert query["response_type"] == ["code"]
    assert query["client_id"] == ["client-123"]
    assert query["scope"] == ["openid email profile"]
    assert query["redirect_uri"] == ["http://testserver/accounts/callback/"]
    assert query["identity_provider"] == ["Google"]
    assert response["Cache-Control"] == "no-store"


@pytest.mark.django_db
def test_login_fails_loudly_when_cognito_unconfigured(client, settings):
    settings.COGNITO_CLIENT_ID = ""
    settings.COGNITO_DOMAIN = ""
    settings.COGNITO_USER_POOL_ID = ""
    response = client.get("/accounts/login/")
    assert response.status_code == 500
    assert response["Cache-Control"] == "no-store"
    body = response.content.decode()
    assert "COGNITO_CLIENT_ID" in body
    assert "COGNITO_DOMAIN" in body
    assert "COGNITO_USER_POOL_ID" in body


@pytest.mark.django_db
def test_login_falls_back_to_dev_login_under_debug(client, settings):
    # adr-10 rule 6: with Cognito unconfigured but DEBUG dev auth active, the
    # login entrypoint routes to the dev path instead of dead-ending on 500 —
    # what makes localhost usable with no cloud config.
    settings.COGNITO_CLIENT_ID = ""
    settings.COGNITO_DOMAIN = ""
    settings.COGNITO_USER_POOL_ID = ""
    settings.DEBUG = True
    settings.AUTH_DEV_MODE = True
    clear_url_caches()
    importlib.reload(apps.users.urls)
    importlib.reload(config.urls)
    try:
        response = client.get("/accounts/login/")
        assert response.status_code == 302
        assert response["Location"] == "/accounts/dev-login/"
        assert response["Cache-Control"] == "no-store"
    finally:
        settings.DEBUG = False
        settings.AUTH_DEV_MODE = False
        clear_url_caches()
        importlib.reload(apps.users.urls)
        importlib.reload(config.urls)


@pytest.mark.django_db
def test_login_issues_state(client, settings):
    settings.COGNITO_DOMAIN = "https://auth.example.com"
    settings.COGNITO_CLIENT_ID = "client-123"
    settings.COGNITO_USER_POOL_ID = "pool-789"
    client.get("/accounts/login/")
    assert client.session.get(oidc.STATE_SESSION_KEY)


@pytest.mark.django_db
def test_callback_opens_django_session(client, monkeypatch):
    _mock_ok(monkeypatch)
    state = _prime_state(client)
    response = client.get(f"/accounts/callback/?code=abc&state={state}")
    assert response.status_code == 302
    assert "_auth_user_id" in client.session
    assert response["Cache-Control"] == "no-store"


@pytest.mark.django_db
def test_callback_lands_on_login_redirect_url(client, monkeypatch, settings):
    settings.LOGIN_REDIRECT_URL = "http://localhost:4321/"
    _mock_ok(monkeypatch)
    state = _prime_state(client)
    response = client.get(f"/accounts/callback/?code=abc&state={state}")
    assert response["Location"] == "http://localhost:4321/"


@pytest.mark.django_db
def test_callback_mirrors_identity_claims(client, monkeypatch):
    _mock_ok(monkeypatch)
    state = _prime_state(client)
    client.get(f"/accounts/callback/?code=abc&state={state}")
    user = User.objects.get(pk=SUB)
    assert user.email == CLAIMS["email"]
    assert user.given_name == CLAIMS["given_name"]
    assert user.family_name == CLAIMS["family_name"]


@pytest.mark.django_db
def test_callback_idempotent_on_sub(client, monkeypatch):
    _mock_ok(monkeypatch)
    for _ in range(2):
        state = _prime_state(client)
        client.get(f"/accounts/callback/?code=abc&state={state}")
    assert User.objects.filter(pk=SUB).count() == 1


@pytest.mark.django_db
def test_callback_rejects_bad_state(client, monkeypatch):
    _mock_ok(monkeypatch)
    _prime_state(client, "expected")
    response = client.get("/accounts/callback/?code=abc&state=wrong")
    assert response.status_code == 400
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_callback_rejects_invalid_token(client, monkeypatch):
    monkeypatch.setattr(oidc, "exchange_code", lambda code, redirect_uri: {"id_token": "mock"})

    def _boom(id_token):
        raise ValueError("token verification failed")

    monkeypatch.setattr(oidc, "verify_id_token", _boom)
    state = _prime_state(client)
    response = client.get(f"/accounts/callback/?code=abc&state={state}")
    assert response.status_code == 400
    assert "_auth_user_id" not in client.session
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_callback_merges_userinfo_picture(client, monkeypatch):
    # The ID token never carries `picture` for a Google-federated user; only
    # /oauth2/userInfo does. The view must merge it in before mirroring.
    _mock_ok(monkeypatch)
    monkeypatch.setattr(
        oidc,
        "exchange_code",
        lambda code, redirect_uri: {"id_token": "mock", "access_token": "at-123"},
    )
    monkeypatch.setattr(
        oidc, "fetch_userinfo", lambda access_token: {"picture": "https://example.com/avatar.png"}
    )
    state = _prime_state(client)
    client.get(f"/accounts/callback/?code=abc&state={state}")
    user = User.objects.get(pk=SUB)
    assert user.picture == "https://example.com/avatar.png"


@pytest.mark.django_db
def test_callback_survives_userinfo_failure(client, monkeypatch):
    # A missing/erroring userInfo call must degrade to the initials fallback,
    # never break login.
    _mock_ok(monkeypatch)
    monkeypatch.setattr(
        oidc,
        "exchange_code",
        lambda code, redirect_uri: {"id_token": "mock", "access_token": "at-123"},
    )

    def _boom(access_token):
        raise TimeoutError("userinfo unreachable")

    monkeypatch.setattr(oidc, "fetch_userinfo", _boom)
    state = _prime_state(client)
    response = client.get(f"/accounts/callback/?code=abc&state={state}")
    assert response.status_code == 302
    assert "_auth_user_id" in client.session
    user = User.objects.get(pk=SUB)
    assert user.picture == ""


@pytest.mark.django_db
def test_callback_ignores_cognito_authority_claims(client, monkeypatch):
    hostile = dict(CLAIMS)
    hostile["cognito:groups"] = ["admins"]
    hostile["custom:role"] = "admin"
    _mock_ok(monkeypatch, hostile)
    state = _prime_state(client)
    client.get(f"/accounts/callback/?code=abc&state={state}")
    user = User.objects.get(pk=SUB)
    assert user.groups.count() == 0
    assert user.is_superuser is False
    assert user.is_staff is False


@pytest.mark.django_db
def test_logout_flushes_and_redirects(client, monkeypatch, settings):
    settings.COGNITO_DOMAIN = "https://auth.example.com"
    settings.COGNITO_CLIENT_ID = "client-123"
    _mock_ok(monkeypatch)
    state = _prime_state(client)
    client.get(f"/accounts/callback/?code=abc&state={state}")
    assert "_auth_user_id" in client.session
    response = client.post("/accounts/logout/")
    assert response.status_code == 302
    assert response["Location"].startswith("https://auth.example.com/logout")
    assert "_auth_user_id" not in client.session
    assert response["Cache-Control"] == "no-store"


@pytest.mark.django_db
def test_logout_skips_cognito_when_domain_absent(client, settings):
    # Local dev: no Cognito hosted-UI to sign out of — land straight back on
    # the app instead of building a broken /logout redirect.
    settings.COGNITO_DOMAIN = ""
    settings.LOGOUT_REDIRECT_URL = "http://localhost:4321/"
    response = client.post("/accounts/logout/")
    assert response.status_code == 302
    assert response["Location"] == "http://localhost:4321/"
    assert response["Cache-Control"] == "no-store"


@pytest.mark.django_db
def test_logout_safe_without_session(client, settings):
    settings.COGNITO_DOMAIN = "https://auth.example.com"
    settings.COGNITO_CLIENT_ID = "client-123"
    response = client.post("/accounts/logout/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_logout_rejects_get(client, monkeypatch, settings):
    settings.COGNITO_DOMAIN = "https://auth.example.com"
    settings.COGNITO_CLIENT_ID = "client-123"
    _mock_ok(monkeypatch)
    state = _prime_state(client)
    client.get(f"/accounts/callback/?code=abc&state={state}")
    response = client.get("/accounts/logout/")
    assert response.status_code == 405
    assert "_auth_user_id" in client.session


@pytest.mark.django_db
def test_logout_post_requires_csrf_token(settings):
    settings.COGNITO_DOMAIN = "https://auth.example.com"
    settings.COGNITO_CLIENT_ID = "client-123"
    from django.test import Client

    strict = Client(enforce_csrf_checks=True)
    response = strict.post("/accounts/logout/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_dev_login_matches_real_session(client, settings):
    settings.DEBUG = True
    settings.AUTH_DEV_MODE = True
    settings.LOGIN_REDIRECT_URL = "http://localhost:4321/"
    settings.AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
        "apps.users.backends.DevLoginBackend",
    ]
    clear_url_caches()
    importlib.reload(apps.users.urls)
    importlib.reload(config.urls)
    try:
        response = client.get("/accounts/dev-login/?email=dev@example.com")
        assert response.status_code == 302
        assert response["Location"] == "http://localhost:4321/"
        assert "_auth_user_id" in client.session
        assert User.objects.filter(email="dev@example.com").exists()
        assert response["Cache-Control"] == "no-store"
    finally:
        settings.DEBUG = False
        settings.AUTH_DEV_MODE = False
        clear_url_caches()
        importlib.reload(apps.users.urls)
        importlib.reload(config.urls)


def test_dev_login_absent_when_not_debug(client, settings):
    assert settings.DEBUG is False
    assert "apps.users.backends.DevLoginBackend" not in settings.AUTHENTICATION_BACKENDS
    with pytest.raises(NoReverseMatch):
        reverse("accounts:dev-login")
    assert client.get("/accounts/dev-login/").status_code == 404


def test_dev_login_absent_when_flag_off_even_under_debug(client, settings):
    settings.DEBUG = True
    settings.AUTH_DEV_MODE = False
    clear_url_caches()
    importlib.reload(apps.users.urls)
    importlib.reload(config.urls)
    try:
        with pytest.raises(NoReverseMatch):
            reverse("accounts:dev-login")
        assert client.get("/accounts/dev-login/").status_code == 404
    finally:
        settings.DEBUG = False
        clear_url_caches()
        importlib.reload(apps.users.urls)
        importlib.reload(config.urls)


def test_check_deploy_fails_when_dev_mode_in_prod(settings):
    settings.AUTH_DEV_MODE = True
    settings.DEBUG = False
    errors = checks.check_auth_hard_guards(app_configs=None)
    assert any(isinstance(e, Error) and e.id == "users.E001" for e in errors)
    with pytest.raises(SystemCheckError):
        call_command("check", deploy=True)


def test_check_deploy_fails_when_debug_true(settings):
    settings.AUTH_DEV_MODE = False
    settings.DEBUG = True
    errors = checks.check_auth_hard_guards(app_configs=None)
    assert any(isinstance(e, Error) and e.id == "users.E002" for e in errors)
    with pytest.raises(SystemCheckError):
        call_command("check", deploy=True)


def test_check_deploy_fails_when_dev_mode_even_under_debug(settings):
    settings.AUTH_DEV_MODE = True
    settings.DEBUG = True
    errors = checks.check_auth_hard_guards(app_configs=None)
    ids = {e.id for e in errors}
    assert {"users.E001", "users.E002"} <= ids


def test_check_deploy_passes_when_guard_satisfied(settings):
    settings.AUTH_DEV_MODE = False
    settings.DEBUG = False
    assert checks.check_auth_hard_guards(app_configs=None) == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/accounts/login/"), ("post", "/accounts/logout/")],
)
def test_accounts_routes_are_no_store(client, settings, method, path):
    settings.COGNITO_DOMAIN = "https://auth.example.com"
    settings.COGNITO_CLIENT_ID = "client-123"
    response = getattr(client, method)(path)
    assert response["Cache-Control"] == "no-store"


@pytest.mark.django_db
def test_login_builds_https_redirect_uri_behind_alb(client, settings):
    settings.COGNITO_DOMAIN = "https://auth.example.com"
    settings.COGNITO_CLIENT_ID = "client-123"
    settings.COGNITO_USER_POOL_ID = "pool-789"
    settings.SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    response = client.get("/accounts/login/", HTTP_X_FORWARDED_PROTO="https")
    query = parse_qs(urlparse(response["Location"]).query)
    redirect_uri = urlparse(query["redirect_uri"][0])
    assert redirect_uri.scheme == "https"
    assert redirect_uri.path == "/accounts/callback/"


@pytest.mark.django_db
def test_hsts_header_present_on_secure_request_without_debug(client, settings):
    settings.SECURE_HSTS_SECONDS = 3600
    settings.SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    response = client.get("/api/health/", secure=True)
    assert response["Strict-Transport-Security"] == "max-age=3600"


@pytest.mark.django_db
def test_hsts_header_absent_when_hsts_seconds_unset(client, settings):
    settings.SECURE_HSTS_SECONDS = 0
    response = client.get("/api/health/", secure=True)
    assert not response.has_header("Strict-Transport-Security")
