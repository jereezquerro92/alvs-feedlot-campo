"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import RequestFactory

from apps.router.admin import RESTRICTED_FIELDS, ROUTER_AUDITORS_GROUP, IntentQueryAdmin
from apps.router.models import IntentQuery

pytestmark = pytest.mark.django_db

User = get_user_model()


def _admin_and_request(user):
    request = RequestFactory().get("/admin/router/intentquery/")
    request.user = user
    return IntentQueryAdmin(IntentQuery, AdminSite()), request


def test_non_router_auditor_cannot_see_restricted_fields():
    user = User.objects.create_user(sub="sub-plain-admin", is_staff=True)
    admin_instance, request = _admin_and_request(user)

    fields = admin_instance.get_fields(request)

    for restricted in RESTRICTED_FIELDS:
        assert restricted not in fields


def test_router_auditor_group_member_sees_restricted_fields():
    group, _ = Group.objects.get_or_create(name=ROUTER_AUDITORS_GROUP)
    user = User.objects.create_user(sub="sub-auditor-admin", is_staff=True)
    user.groups.add(group)
    admin_instance, request = _admin_and_request(user)

    fields = admin_instance.get_fields(request)

    for restricted in RESTRICTED_FIELDS:
        assert restricted in fields


def test_router_auditors_group_seeded_by_migration():
    assert Group.objects.filter(name=ROUTER_AUDITORS_GROUP).exists()
