"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
API: [[API]]
LIVE-DOC:END"""

import json
import secrets
import urllib.parse
import urllib.request
from functools import lru_cache

import jwt
from django.conf import settings
from jwt import PyJWKClient

STATE_SESSION_KEY = "oidc_state"

TOKEN_EXCHANGE_TIMEOUT_SECONDS = 10


def new_state():
    return secrets.token_urlsafe(32)


def build_authorize_url(redirect_uri, state):
    query = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": settings.COGNITO_CLIENT_ID,
            "scope": "openid email profile",
            "redirect_uri": redirect_uri,
            "state": state,
            "identity_provider": "Google",
        }
    )
    return f"{settings.COGNITO_DOMAIN}/oauth2/authorize?{query}"


def build_logout_url(logout_uri):
    query = urllib.parse.urlencode(
        {"client_id": settings.COGNITO_CLIENT_ID, "logout_uri": logout_uri}
    )
    return f"{settings.COGNITO_DOMAIN}/logout?{query}"


def exchange_code(code, redirect_uri):
    body = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "client_id": settings.COGNITO_CLIENT_ID,
            "client_secret": settings.COGNITO_CLIENT_SECRET,
            "code": code,
            "redirect_uri": redirect_uri,
        }
    ).encode()
    request = urllib.request.Request(
        f"{settings.COGNITO_DOMAIN}/oauth2/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(
        request, timeout=TOKEN_EXCHANGE_TIMEOUT_SECONDS
    ) as response:
        return json.loads(response.read())


def fetch_userinfo(access_token):
    """Cognito's ID token does not carry federated-IdP attributes such as
    `picture`; they are only exposed via this endpoint. Callers must treat
    failure here as non-fatal — login must succeed even if this call fails."""
    request = urllib.request.Request(
        f"{settings.COGNITO_DOMAIN}/oauth2/userInfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    with urllib.request.urlopen(
        request, timeout=TOKEN_EXCHANGE_TIMEOUT_SECONDS
    ) as response:
        return json.loads(response.read())


def _issuer():
    return (
        f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
        f"{settings.COGNITO_USER_POOL_ID}"
    )


@lru_cache(maxsize=1)
def _jwks_client(jwks_uri):
    return PyJWKClient(jwks_uri)


def verify_id_token(id_token):
    issuer = _issuer()
    signing_key = _jwks_client(f"{issuer}/.well-known/jwks.json").get_signing_key_from_jwt(
        id_token
    )
    claims = jwt.decode(
        id_token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.COGNITO_CLIENT_ID,
        issuer=issuer,
        options={"require": ["exp", "iat", "iss", "aud", "sub"]},
    )
    if claims.get("token_use") != "id":
        raise jwt.InvalidTokenError("token_use is not 'id'")
    return claims
