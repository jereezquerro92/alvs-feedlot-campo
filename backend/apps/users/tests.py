"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.core.management import call_command
from django.db import IntegrityError, connection

User = get_user_model()

SUB = "11111111-1111-1111-1111-111111111111"
MIRROR = {
    "email": "user@example.com",
    "given_name": "Ada",
    "family_name": "Lovelace",
}


def test_auth_user_model_is_users_user(settings):
    assert settings.AUTH_USER_MODEL == "users.User"


def test_sub_is_identity_key():
    assert User._meta.pk.name == "sub"


@pytest.mark.django_db
def test_sub_is_unique():
    User.objects.create(sub=SUB, **MIRROR)
    with pytest.raises(IntegrityError):
        User.objects.create(sub=SUB, email="other@example.com")


def test_cognito_mirror_fields_exist():
    for name in ("email", "given_name", "family_name"):
        assert User._meta.get_field(name) is not None


def test_forbidden_identity_field_names_absent():
    for forbidden in ("cognito_id", "uid", "user_uuid"):
        with pytest.raises(FieldDoesNotExist):
            User._meta.get_field(forbidden)


@pytest.mark.django_db
def test_get_or_create_by_sub():
    first, created = User.objects.get_or_create(sub=SUB, defaults=MIRROR)
    assert created is True
    again, created_again = User.objects.get_or_create(sub=SUB, defaults=MIRROR)
    assert created_again is False
    assert again.pk == first.pk
    assert User.objects.count() == 1


def test_user_has_groups_relation():
    assert User._meta.get_field("groups") is not None


@pytest.mark.django_db
def test_no_password_auth_dependency():
    user, _ = User.objects.get_or_create(sub=SUB, defaults=MIRROR)
    assert user.has_usable_password() is False


@pytest.mark.django_db
def test_initial_migration_applies_clean():
    table = User._meta.db_table
    with connection.cursor() as cursor:
        columns = connection.introspection.get_table_description(cursor, table)
    names = {column.name for column in columns}
    assert {"sub", "email", "given_name", "family_name"} <= names


@pytest.mark.django_db
def test_makemigrations_check_clean():
    call_command("makemigrations", "users", check=True, dry_run=True, verbosity=0)


@pytest.mark.django_db
def test_user_roundtrip_persists():
    User.objects.create(sub=SUB, **MIRROR)
    reloaded = User.objects.get(pk=SUB)
    assert reloaded.sub == SUB
    assert reloaded.email == MIRROR["email"]
    assert reloaded.given_name == MIRROR["given_name"]
    assert reloaded.family_name == MIRROR["family_name"]
