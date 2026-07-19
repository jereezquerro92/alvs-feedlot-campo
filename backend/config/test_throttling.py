"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-02-initial-stack]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Tests for CooldownThrottle (docs/tdds/tdd-01-cooldown-throttle.md)."""

import time

import pytest
from django.core.management import call_command
from django.urls import path
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.throttling import CooldownThrottle

MODEL_BACKEND = "django.contrib.auth.backends.ModelBackend"


class _CooldownProbeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [CooldownThrottle]

    def get(self, request):
        return Response({"ok": True})


urlpatterns = [path("cooldown-probe/", _CooldownProbeView.as_view())]

pytestmark = [pytest.mark.django_db, pytest.mark.urls(__name__)]


def _user(django_user_model, sub):
    return django_user_model.objects.create(sub=sub, email=f"{sub}@example.com")


@pytest.fixture(autouse=True)
def _cache_table():
    call_command("createcachetable")


def test_second_call_within_window_is_rejected_with_429(client, settings, django_user_model):
    settings.THROTTLE_COOLDOWN_SECONDS = 60
    user = _user(django_user_model, "cooldown-user-1")
    client.force_login(user, backend=MODEL_BACKEND)

    first = client.get("/cooldown-probe/")
    second = client.get("/cooldown-probe/")

    assert first.status_code == 200
    assert second.status_code == 429
    assert "Retry-After" in second
    assert second["Cache-Control"] == "no-store"


def test_call_after_window_succeeds(client, settings, django_user_model):
    settings.THROTTLE_COOLDOWN_SECONDS = 1
    user = _user(django_user_model, "cooldown-user-2")
    client.force_login(user, backend=MODEL_BACKEND)

    first = client.get("/cooldown-probe/")
    time.sleep(1.1)
    second = client.get("/cooldown-probe/")

    assert first.status_code == 200
    assert second.status_code == 200


def test_window_read_from_settings_disables_when_zero(client, settings, django_user_model):
    settings.THROTTLE_COOLDOWN_SECONDS = 0
    user = _user(django_user_model, "cooldown-user-3")
    client.force_login(user, backend=MODEL_BACKEND)

    first = client.get("/cooldown-probe/")
    second = client.get("/cooldown-probe/")

    assert first.status_code == 200
    assert second.status_code == 200


def test_two_different_users_do_not_share_a_cooldown(client, settings, django_user_model):
    from django.test import Client

    settings.THROTTLE_COOLDOWN_SECONDS = 60
    user_a = _user(django_user_model, "cooldown-user-4")
    user_b = _user(django_user_model, "cooldown-user-5")

    client.force_login(user_a, backend=MODEL_BACKEND)
    client.get("/cooldown-probe/")

    other_client = Client()
    other_client.force_login(user_b, backend=MODEL_BACKEND)
    second = other_client.get("/cooldown-probe/")

    assert second.status_code == 200
