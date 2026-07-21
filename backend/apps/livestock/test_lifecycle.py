"""Phase 2: the animal lifecycle — weighings, growth, deaths and exits."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.clients.models import Client
from apps.ledger.models import LedgerEntry
from apps.livestock.models import Animal, Exit, Lot
from apps.livestock.services import (
    create_lot_intake,
    growth_series,
    register_death,
    register_exit,
    register_weighing,
)

pytestmark = pytest.mark.django_db


def _client():
    return Client.objects.create(name="La Esperanza", kind=Client.Kind.BOARDING)


def _animal(client, ear_tag="A-001", weight="320"):
    return Animal.objects.create(
        client=client, ear_tag=ear_tag, category="steer", sex="male",
        entry_date="2026-01-10", entry_weight=Decimal(weight), current_weight=Decimal(weight),
    )


def _lot(client, head=50, total="16000"):
    _, lot = create_lot_intake(
        client=client, date="2026-01-10", code="L-01", head_count=head, total_weight=total
    )
    return lot


# --- weighings ---------------------------------------------------------------

def test_weighing_updates_animal_current_weight():
    animal = _animal(_client())
    register_weighing(animal=animal, weight="368", date="2026-03-01")
    animal.refresh_from_db()
    assert animal.current_weight == Decimal("368.00")


def test_weighing_updates_lot_total_weight():
    lot = _lot(_client())
    register_weighing(lot=lot, weight="18500", date="2026-03-01")
    lot.refresh_from_db()
    assert lot.total_weight == Decimal("18500.00")


def test_weighing_on_dead_animal_is_rejected():
    client = _client()
    animal = _animal(client)
    register_death(animal=animal, date="2026-02-01")
    animal.refresh_from_db()
    with pytest.raises(ValidationError):
        register_weighing(animal=animal, weight="380", date="2026-03-01")


def test_weighing_before_entry_date_is_rejected():
    animal = _animal(_client())
    with pytest.raises(ValidationError):
        register_weighing(animal=animal, weight="300", date="2026-01-01")


def test_weighing_requires_exactly_one_target():
    client = _client()
    animal, lot = _animal(client), _lot(client)
    with pytest.raises(ValidationError):
        register_weighing(animal=animal, lot=lot, weight="300", date="2026-03-01")
    with pytest.raises(ValidationError):
        register_weighing(weight="300", date="2026-03-01")


# --- growth ------------------------------------------------------------------

def test_adg_between_two_animal_weighings():
    animal = _animal(_client())
    register_weighing(animal=animal, weight="320", date="2026-02-01")
    register_weighing(animal=animal, weight="380", date="2026-04-02")  # 60 days, +60 kg
    series = growth_series(animal=animal)
    assert series[0]["adg"] is None  # nothing to compare against
    assert series[1]["adg"] == Decimal("1")


def test_lot_adg_uses_weight_per_head_not_total():
    lot = _lot(_client(), head=50, total="16000")
    register_weighing(lot=lot, weight="16000", date="2026-02-01", head_count=50)  # 320/head
    register_weighing(lot=lot, weight="17500", date="2026-03-03", head_count=50)  # 350/head
    series = growth_series(lot=lot)
    # 30 kg per head over 30 days = 1.0, not (1500/30) = 50.
    assert series[1]["adg"] == Decimal("1")


def test_lot_adg_not_calculable_when_head_count_changed():
    lot = _lot(_client(), head=50, total="16000")
    register_weighing(lot=lot, weight="16000", date="2026-02-01", head_count=50)
    register_weighing(lot=lot, weight="20000", date="2026-03-03", head_count=62)
    series = growth_series(lot=lot)
    assert series[1]["adg"] is None
    assert series[1]["not_calculable"] == "head_count_changed"


# --- deaths ------------------------------------------------------------------

def test_death_marks_animal_dead():
    animal = _animal(_client())
    register_death(animal=animal, date="2026-03-01", cause="disease")
    animal.refresh_from_db()
    assert animal.status == Animal.Status.DEAD


def test_partial_lot_death_reduces_head_and_weight():
    lot = _lot(_client(), head=50, total="16000")
    register_death(lot=lot, date="2026-03-01", head_count=3, weight="960")
    lot.refresh_from_db()
    assert lot.head_count == 47
    assert lot.total_weight == Decimal("15040.00")


def test_death_of_more_head_than_alive_is_rejected():
    lot = _lot(_client(), head=10, total="3200")
    with pytest.raises(ValidationError):
        register_death(lot=lot, date="2026-03-01", head_count=11)


def test_death_does_not_touch_the_ledger():
    client = _client()
    animal = _animal(client)
    register_death(animal=animal, date="2026-03-01")
    assert LedgerEntry.objects.filter(account=client.account).count() == 0


# --- exits -------------------------------------------------------------------

def test_sale_marks_animal_sold():
    animal = _animal(_client())
    register_exit(animal=animal, date="2026-06-01", kind=Exit.Kind.SALE, sale_price_per_kg="2400")
    animal.refresh_from_db()
    assert animal.status == Animal.Status.SOLD


def test_transfer_marks_animal_exited():
    animal = _animal(_client())
    register_exit(animal=animal, date="2026-06-01", kind=Exit.Kind.TRANSFER)
    animal.refresh_from_db()
    assert animal.status == Animal.Status.EXITED


def test_partial_lot_exit_reduces_head():
    lot = _lot(_client(), head=50, total="16000")
    register_exit(lot=lot, date="2026-06-01", head_count=20, weight="7000")
    lot.refresh_from_db()
    assert lot.head_count == 30
    assert lot.status == Lot.Status.ACTIVE


def test_full_lot_exit_closes_the_lot():
    lot = _lot(_client(), head=50, total="16000")
    register_exit(lot=lot, date="2026-06-01", head_count=50, weight="17500")
    lot.refresh_from_db()
    assert lot.head_count == 0
    assert lot.status == Lot.Status.CLOSED


def test_exit_does_not_touch_the_ledger():
    client = _client()
    animal = _animal(client)
    register_exit(animal=animal, date="2026-06-01", sale_price_per_kg="2400")
    assert LedgerEntry.objects.filter(account=client.account).count() == 0
