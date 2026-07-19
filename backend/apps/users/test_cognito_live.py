"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

import base64
import hashlib
import hmac
import json
import os

import pytest

from apps.users import oidc
from apps.users.models import User
from apps.users.services import upsert_user_from_claims

pytestmark = pytest.mark.cognito_live

SECRET_ID = f"alvs/prod/{os.environ.get('PROJECT_SLUG', 'astro-drf-aws')}/cognito"
CLIENT_ID = "3t2mknigno1jmtp68si4dj31bi"


def _secret_hash(username, client_id, client_secret):
    message = (username + client_id).encode()
    digest = hmac.new(client_secret.encode(), message, hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


@pytest.fixture(scope="module")
def cognito():
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        pytest.skip("boto3 not installed")

    try:
        sm = boto3.client("secretsmanager", region_name="us-east-1")
        cfg = json.loads(sm.get_secret_value(SecretId=SECRET_ID)["SecretString"])
    except (BotoCoreError, ClientError) as exc:
        pytest.skip(f"Cognito secret {SECRET_ID} unavailable: {type(exc).__name__}")

    username = cfg["TEST_USER_EMAIL"]
    idp = boto3.client("cognito-idp", region_name=cfg["COGNITO_REGION"])
    try:
        result = idp.admin_initiate_auth(
            UserPoolId=cfg["COGNITO_USER_POOL_ID"],
            ClientId=CLIENT_ID,
            AuthFlow="ADMIN_USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": username,
                "PASSWORD": cfg["TEST_USER_PASSWORD"],
                "SECRET_HASH": _secret_hash(
                    username, CLIENT_ID, cfg["COGNITO_CLIENT_SECRET"]
                ),
            },
        )
    except (BotoCoreError, ClientError) as exc:
        pytest.skip(f"admin-initiate-auth failed: {type(exc).__name__}")

    return {
        "id_token": result["AuthenticationResult"]["IdToken"],
        "region": cfg["COGNITO_REGION"],
        "pool": cfg["COGNITO_USER_POOL_ID"],
        "email": username,
    }


@pytest.fixture
def _live_settings(cognito, settings):
    settings.COGNITO_REGION = cognito["region"]
    settings.COGNITO_USER_POOL_ID = cognito["pool"]
    settings.COGNITO_CLIENT_ID = CLIENT_ID


def test_verify_id_token_accepts_live_token(cognito, _live_settings):
    claims = oidc.verify_id_token(cognito["id_token"])
    issuer = (
        f"https://cognito-idp.{cognito['region']}.amazonaws.com/{cognito['pool']}"
    )
    assert claims["iss"] == issuer
    assert claims["aud"] == CLIENT_ID
    assert claims["token_use"] == "id"


def test_live_token_maps_identity_claims(cognito, _live_settings):
    claims = oidc.verify_id_token(cognito["id_token"])
    assert claims["sub"]
    assert claims["email"] == cognito["email"]
    assert claims["given_name"] == "Plain"
    assert claims["family_name"] == "Test"


@pytest.mark.django_db
def test_live_token_upserts_user_via_callback_path(cognito, _live_settings):
    claims = oidc.verify_id_token(cognito["id_token"])
    user = upsert_user_from_claims(claims)
    assert user.pk == claims["sub"]
    assert User.objects.get(pk=claims["sub"]).email == cognito["email"]
    assert user.given_name == "Plain"
    assert user.family_name == "Test"
    assert user.groups.count() == 0
    assert user.is_staff is False
    assert user.is_superuser is False
