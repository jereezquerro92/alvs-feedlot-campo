from decimal import Decimal

import pytest

from apps.clients.models import Client
from apps.livestock.models import Animal, Intake, Lot
from apps.livestock.services import create_individual_intake, create_lot_intake

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
