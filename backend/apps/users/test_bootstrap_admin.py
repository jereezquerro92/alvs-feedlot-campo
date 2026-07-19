"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()


@pytest.mark.django_db
def test_creates_superuser_from_env(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", "root@example.com")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "correct-horse-battery-staple")

    call_command("bootstrap_admin")

    user = User.objects.get(sub="bootstrap-admin")
    assert user.email == "root@example.com"
    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.has_usable_password() is True


@pytest.mark.django_db
def test_idempotent_and_rotates_password(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", "root@example.com")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "first-password")
    call_command("bootstrap_admin")

    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "second-password")
    call_command("bootstrap_admin")

    assert User.objects.count() == 1
    user = User.objects.get(sub="bootstrap-admin")
    assert user.check_password("first-password") is False
    assert user.check_password("second-password") is True


@pytest.mark.django_db
def test_skips_cleanly_when_vars_absent(monkeypatch):
    monkeypatch.delenv("DJANGO_SUPERUSER_EMAIL", raising=False)
    monkeypatch.delenv("DJANGO_SUPERUSER_PASSWORD", raising=False)

    call_command("bootstrap_admin")

    assert User.objects.count() == 0


def test_command_is_registered():
    from apps.users.management.commands.bootstrap_admin import Command

    assert Command is not None
