"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Phase 13: the sanitary plan, its immutable enrollment, and the derived calendar.

The plan is a reusable template; enrolling a target is an immutable event that posts
NO ledger entry (billing stays with HealthEvent, adr-40 decision 4); the applied /
pending / upcoming status of each dose is derived by crossing the schedule against the
existing HealthEvents (adr-40 decision 3).
"""

from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.clients.models import Client
from apps.ledger.models import LedgerEntry
from apps.livestock.models import Animal
from apps.sanitary.models import HealthProduct, PlanEnrollment, SanitaryPlan
from apps.sanitary.services import (
    enroll_in_plan,
    plan_schedule_for_client,
    register_health_event,
)

pytestmark = pytest.mark.django_db


def _fixtures():
    client = Client.objects.create(name="La Esperanza", kind=Client.Kind.BOARDING)
    product = HealthProduct.objects.create(
        name="Aftosa", kind=HealthProduct.Kind.VACCINE, unit_price=Decimal("1500")
    )
    animal = Animal.objects.create(
        client=client, ear_tag="A-001", category="steer", entry_date="2026-01-10"
    )
    return client, product, animal


def _plan_with_items(product, offsets):
    plan = SanitaryPlan.objects.create(name="Plan de entrada")
    for off in offsets:
        plan.items.create(product=product, day_offset=off, dose=Decimal("1"))
    return plan


def test_enroll_in_plan_creates_immutable_event_and_posts_no_ledger():
    client, product, animal = _fixtures()
    plan = _plan_with_items(product, [0, 30])
    enrollment = enroll_in_plan(
        plan=plan, client=client, animal=animal, start_date="2026-03-01"
    )
    assert PlanEnrollment.objects.filter(id=enrollment.id).exists()
    # A plan/enrollment is intent, not an applied input: zero ledger entries.
    assert LedgerEntry.objects.filter(account=client.account).count() == 0


def test_enroll_requires_exactly_one_target():
    client, product, _ = _fixtures()
    plan = _plan_with_items(product, [0])
    with pytest.raises(ValidationError):
        enroll_in_plan(plan=plan, client=client, start_date="2026-03-01")


def test_enroll_rejects_foreign_target():
    client, product, _ = _fixtures()
    plan = _plan_with_items(product, [0])
    other = Client.objects.create(name="El Ombú", kind=Client.Kind.BOARDING)
    foreign = Animal.objects.create(
        client=other, ear_tag="B-001", category="steer", entry_date="2026-01-10"
    )
    with pytest.raises(ValidationError):
        enroll_in_plan(plan=plan, client=client, animal=foreign, start_date="2026-03-01")


def test_enroll_rejects_inactive_target():
    client, product, animal = _fixtures()
    animal.status = Animal.Status.DEAD
    animal.save()
    plan = _plan_with_items(product, [0])
    with pytest.raises(ValidationError):
        enroll_in_plan(plan=plan, client=client, animal=animal, start_date="2026-03-01")


def test_enroll_rejects_inactive_plan():
    client, product, animal = _fixtures()
    plan = _plan_with_items(product, [0])
    plan.is_active = False
    plan.save()
    with pytest.raises(ValidationError):
        enroll_in_plan(plan=plan, client=client, animal=animal, start_date="2026-03-01")


def test_schedule_marks_due_dose_pending_and_future_dose_upcoming():
    client, product, animal = _fixtures()
    plan = _plan_with_items(product, [0, 30])
    enroll_in_plan(plan=plan, client=client, animal=animal, start_date="2026-03-01")

    result = plan_schedule_for_client(client, as_of=date(2026, 3, 10))
    by_offset = {item["day_offset"]: item for item in result["items"]}
    assert by_offset[0]["status"] == "pending"
    assert by_offset[0]["due_date"] == "2026-03-01"
    assert by_offset[30]["status"] == "upcoming"
    assert by_offset[30]["due_date"] == "2026-03-31"
    assert result["pending_count"] == 1


def test_schedule_marks_applied_when_matching_health_event_exists():
    client, product, animal = _fixtures()
    plan = _plan_with_items(product, [0, 30])
    enroll_in_plan(plan=plan, client=client, animal=animal, start_date="2026-03-01")
    # The first dose gets applied on the ground (a real HealthEvent).
    register_health_event(
        client=client, product=product, animal=animal, quantity="1", date="2026-03-02"
    )

    result = plan_schedule_for_client(client, as_of=date(2026, 3, 10))
    by_offset = {item["day_offset"]: item for item in result["items"]}
    assert by_offset[0]["status"] == "applied"
    assert by_offset[30]["status"] == "upcoming"
    assert result["pending_count"] == 0


def test_schedule_empty_for_client_without_enrollments():
    client, _, _ = _fixtures()
    result = plan_schedule_for_client(client, as_of=date(2026, 3, 10))
    assert result["items"] == []
    assert result["pending_count"] == 0
