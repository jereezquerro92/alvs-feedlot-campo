"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

from decimal import Decimal

import pytest

from apps.clients.models import Client
from apps.livestock.models import Animal, Intake, Lot
from apps.livestock.services import (
    add_to_lot_intake,
    create_individual_intake,
    create_lot_intake,
)

pytestmark = pytest.mark.django_db


def test_individual_intake_creates_animals():
    client = Client.objects.create(name="Ind")
    intake, animals = create_individual_intake(
        client=client,
        date="2026-07-21",
        animals=[
            {"ear_tag": "0001", "category": "steer", "sex": "male", "entry_weight": "320"},
            {"ear_tag": "0002", "category": "heifer", "sex": "female", "entry_weight": "300"},
        ],
    )
    assert intake.mode == Intake.Mode.INDIVIDUAL
    assert intake.head_count == 2
    assert Animal.objects.filter(client=client).count() == 2
    a = Animal.objects.get(ear_tag="0001")
    assert a.current_weight == Decimal("320.00")


def test_lot_intake_creates_anonymous_lot():
    client = Client.objects.create(name="Lote")
    intake, lot = create_lot_intake(
        client=client, date="2026-07-21", code="L-07", head_count=46, total_weight="21850"
    )
    assert intake.mode == Intake.Mode.LOT
    assert lot.mode == Lot.Mode.ANONYMOUS
    assert lot.head_count == 46
    assert lot.total_weight == Decimal("21850.00")


def test_active_ear_tag_unique_per_client():
    from django.db import IntegrityError

    client = Client.objects.create(name="Dup")
    Animal.objects.create(client=client, ear_tag="A1", category="cow", entry_date="2026-07-01")
    with pytest.raises(IntegrityError):
        Animal.objects.create(client=client, ear_tag="A1", category="cow", entry_date="2026-07-02")


def test_lot_code_unique_per_client():
    """A client cannot own two lots with the same code (task #20)."""
    from django.core.exceptions import ValidationError

    client = Client.objects.create(name="UniqLot")
    create_lot_intake(client=client, date="2026-07-21", code="L-07", head_count=10, total_weight="4000")
    with pytest.raises(ValidationError):
        create_lot_intake(
            client=client, date="2026-07-22", code="L-07", head_count=5, total_weight="2000"
        )


def test_same_lot_code_allowed_across_clients():
    """The uniqueness is per client, not global — two clients may reuse a code."""
    a = Client.objects.create(name="ClientA")
    b = Client.objects.create(name="ClientB")
    _, lot_a = create_lot_intake(client=a, date="2026-07-21", code="L-1", head_count=3, total_weight="900")
    _, lot_b = create_lot_intake(client=b, date="2026-07-21", code="L-1", head_count=4, total_weight="1200")
    assert lot_a.id != lot_b.id


def test_add_to_existing_lot_grows_counters():
    """Adding an intake to an existing lot adds to its event-maintained counters."""
    client = Client.objects.create(name="Grow")
    _, lot = create_lot_intake(
        client=client, date="2026-07-21", code="L-08", head_count=40, total_weight="18000"
    )
    intake, updated = add_to_lot_intake(
        client=client, date="2026-07-25", lot=lot, head_count=10, total_weight="5000"
    )
    assert intake.mode == Intake.Mode.LOT
    assert intake.lot_id == lot.id
    updated.refresh_from_db()
    assert updated.head_count == 50
    assert updated.total_weight == Decimal("23000.00")


def test_add_to_lot_rejects_foreign_client():
    """A lot belonging to another client cannot receive an intake."""
    from django.core.exceptions import ValidationError

    owner = Client.objects.create(name="Owner")
    other = Client.objects.create(name="Other")
    _, lot = create_lot_intake(
        client=owner, date="2026-07-21", code="L-09", head_count=5, total_weight="2000"
    )
    with pytest.raises(ValidationError):
        add_to_lot_intake(client=other, date="2026-07-25", lot=lot, head_count=1, total_weight="400")
