"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from apps.router.models import IntentQuery

pytestmark = pytest.mark.django_db

User = get_user_model()


def _make_row(user, age_days):
    row = IntentQuery.objects.create(
        utterance="hi",
        menu_offered=[],
        choice="NO_MATCH",
        model_id="mock",
        user=user,
    )
    IntentQuery.objects.filter(pk=row.pk).update(created_at=timezone.now() - timedelta(days=age_days))
    return row


def test_purge_deletes_rows_older_than_retention_window(settings):
    settings.ROUTER_AUDIT_RETENTION_DAYS = 30
    user = User.objects.create_user(sub="sub-purge")
    old_row = _make_row(user, age_days=40)
    recent_row = _make_row(user, age_days=5)

    call_command("purge_router_audit")

    remaining_ids = set(IntentQuery.objects.values_list("pk", flat=True))
    assert old_row.pk not in remaining_ids
    assert recent_row.pk in remaining_ids


def test_purge_dry_run_deletes_nothing(settings):
    settings.ROUTER_AUDIT_RETENTION_DAYS = 30
    user = User.objects.create_user(sub="sub-dry-run")
    old_row = _make_row(user, age_days=40)

    call_command("purge_router_audit", "--dry-run")

    assert IntentQuery.objects.filter(pk=old_row.pk).exists()


def test_purge_is_idempotent(settings):
    settings.ROUTER_AUDIT_RETENTION_DAYS = 30
    user = User.objects.create_user(sub="sub-idempotent")
    _make_row(user, age_days=40)

    call_command("purge_router_audit")
    call_command("purge_router_audit")

    assert IntentQuery.objects.count() == 0
