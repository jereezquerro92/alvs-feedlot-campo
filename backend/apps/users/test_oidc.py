"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from apps.users import oidc

# Fixed identity for the fake user pool used by every test below. Kept in
# sync with the settings each test applies via the `settings` fixture.
REGION = "us-east-1"
USER_POOL_ID = "us-east-1_test123"
CLIENT_ID = "test-client-id"
ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"


@pytest.fixture(scope="module")
def rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def _base_claims(**overrides):
    now = datetime.now(timezone.utc)
    claims = {
        "sub": "user-sub-123",
        "iss": ISSUER,
        "aud": CLIENT_ID,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "token_use": "id",
        "email": "ada@example.com",
    }
    claims.update(overrides)
    return claims


def _sign(claims, private_key):
    return jwt.encode(claims, private_key, algorithm="RS256")


def _use_pool_settings(settings):
    settings.COGNITO_REGION = REGION
    settings.COGNITO_USER_POOL_ID = USER_POOL_ID
    settings.COGNITO_CLIENT_ID = CLIENT_ID


def _patch_jwks(monkeypatch, public_key):
    """Stand in for PyJWKClient: verify_id_token only needs a signing key
    whose `.key` attribute is a public key object, so we skip the real
    network round-trip to `.well-known/jwks.json` entirely."""

    class _FakeJWKSClient:
        def get_signing_key_from_jwt(self, token):
            return SimpleNamespace(key=public_key)

    monkeypatch.setattr(oidc, "_jwks_client", lambda jwks_uri: _FakeJWKSClient())


def test_verify_id_token_accepts_valid_token(monkeypatch, settings, rsa_keypair):
    private_key, public_key = rsa_keypair
    _use_pool_settings(settings)
    _patch_jwks(monkeypatch, public_key)

    token = _sign(_base_claims(), private_key)

    claims = oidc.verify_id_token(token)

    assert claims["sub"] == "user-sub-123"
    assert claims["iss"] == ISSUER
    assert claims["aud"] == CLIENT_ID
    assert claims["token_use"] == "id"
    assert claims["email"] == "ada@example.com"


def test_verify_id_token_rejects_invalid_signature(monkeypatch, settings, rsa_keypair):
    _, public_key = rsa_keypair
    forged_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _use_pool_settings(settings)
    _patch_jwks(monkeypatch, public_key)

    # Signed with a different keypair than the one exposed via JWKS.
    token = _sign(_base_claims(), forged_private_key)

    with pytest.raises(jwt.InvalidSignatureError):
        oidc.verify_id_token(token)


def test_verify_id_token_rejects_wrong_audience(monkeypatch, settings, rsa_keypair):
    private_key, public_key = rsa_keypair
    _use_pool_settings(settings)
    _patch_jwks(monkeypatch, public_key)

    token = _sign(_base_claims(aud="some-other-client-id"), private_key)

    with pytest.raises(jwt.InvalidAudienceError):
        oidc.verify_id_token(token)


def test_verify_id_token_rejects_wrong_issuer(monkeypatch, settings, rsa_keypair):
    private_key, public_key = rsa_keypair
    _use_pool_settings(settings)
    _patch_jwks(monkeypatch, public_key)

    token = _sign(
        _base_claims(iss="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_evilpool"),
        private_key,
    )

    with pytest.raises(jwt.InvalidIssuerError):
        oidc.verify_id_token(token)


def test_verify_id_token_rejects_expired_token(monkeypatch, settings, rsa_keypair):
    private_key, public_key = rsa_keypair
    _use_pool_settings(settings)
    _patch_jwks(monkeypatch, public_key)

    now = datetime.now(timezone.utc)
    token = _sign(
        _base_claims(
            iat=int((now - timedelta(hours=2)).timestamp()),
            exp=int((now - timedelta(hours=1)).timestamp()),
        ),
        private_key,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        oidc.verify_id_token(token)


def test_verify_id_token_rejects_access_token_use(monkeypatch, settings, rsa_keypair):
    private_key, public_key = rsa_keypair
    _use_pool_settings(settings)
    _patch_jwks(monkeypatch, public_key)

    token = _sign(_base_claims(token_use="access"), private_key)

    with pytest.raises(jwt.InvalidTokenError, match="token_use"):
        oidc.verify_id_token(token)


class _FakeResponse:
    def __init__(self, body):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def read(self):
        return self._body


def test_fetch_userinfo_returns_parsed_json(monkeypatch, settings):
    settings.COGNITO_DOMAIN = "https://auth.example.com"
    captured = {}

    def _fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["auth_header"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        return _FakeResponse(b'{"picture": "https://example.com/avatar.png"}')

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    result = oidc.fetch_userinfo("at-123")

    assert result == {"picture": "https://example.com/avatar.png"}
    assert captured["url"] == "https://auth.example.com/oauth2/userInfo"
    assert captured["auth_header"] == "Bearer at-123"
    assert captured["timeout"] == oidc.TOKEN_EXCHANGE_TIMEOUT_SECONDS


def test_fetch_userinfo_propagates_http_errors(monkeypatch, settings):
    # fetch_userinfo itself does not catch anything; it is the caller's job
    # (see CallbackView) to treat failures as non-fatal per the docstring.
    settings.COGNITO_DOMAIN = "https://auth.example.com"

    def _fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 500, "boom", hdrs=None, fp=None)

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    with pytest.raises(urllib.error.HTTPError):
        oidc.fetch_userinfo("at-123")


def test_fetch_userinfo_failure_is_non_fatal_under_documented_caller_contract(monkeypatch, settings):
    """The docstring says: "Callers must treat failure here as non-fatal —
    login must succeed even if this call fails." CallbackView implements
    that with a bare `except Exception` around the call (apps/users/views.py).
    This reproduces that exact guard, offline and DB-free, to prove any
    failure fetch_userinfo raises is swallowable that way."""
    settings.COGNITO_DOMAIN = "https://auth.example.com"

    def _fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 500, "boom", hdrs=None, fp=None)

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    claims = {"sub": "user-sub-123"}
    try:
        userinfo = oidc.fetch_userinfo("at-123")
        claims = {**claims, **userinfo}
    except Exception:
        pass

    assert claims == {"sub": "user-sub-123"}
