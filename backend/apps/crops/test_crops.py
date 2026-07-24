"""Phase 6 (crops): field tasks bill the client through the ledger's generic seam;
cuttings are production and post nothing (adr-32-multi-rubro-assets)."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.clients.models import Client
from apps.crops.models import Crop, Cutting, Pivot
from apps.crops.services import register_cutting, register_field_task
from apps.ledger.models import Concept, Direction, LedgerEntry

pytestmark = pytest.mark.django_db


def _fixtures():
    client = Client.objects.create(name="Estancia La Alfalfa", kind=Client.Kind.OWN)
    pivot = Pivot.objects.create(client=client, name="Círculo 1", area_ha=Decimal("52"))
    crop = Crop.objects.create(
        pivot=pivot, species=Crop.Species.ALFALFA, sown_date="2026-02-01"
    )
    return client, pivot, crop


def test_field_task_charges_the_account_as_a_service():
    client, pivot, _ = _fixtures()
    task = register_field_task(
        client=client, pivot=pivot, date="2026-03-01", title="Fertilización",
        unit_price="1200", quantity="3",
    )
    entry = LedgerEntry.objects.get(account=client.account)
    assert entry.direction == Direction.DEBIT
    assert entry.concept == Concept.SERVICE
    assert entry.amount == Decimal("3600.00")
    assert entry.source_kind == "field_task"
    assert entry.source_id == task.id
    client.account.refresh_from_db()
    assert client.account.balance_cached == Decimal("3600.00")


def test_field_task_unit_price_is_snapshotted():
    client, pivot, _ = _fixtures()
    task = register_field_task(
        client=client, pivot=pivot, date="2026-03-01", title="Riego", unit_price="900",
    )
    assert task.unit_price == Decimal("900.0000")
    assert task.total_cost == Decimal("900.0000")


def test_field_task_on_another_clients_pivot_is_rejected():
    client, _, _ = _fixtures()
    other = Client.objects.create(name="El Ombú", kind=Client.Kind.BOARDING)
    foreign = Pivot.objects.create(client=other, name="Círculo X")
    with pytest.raises(ValidationError):
        register_field_task(
            client=client, pivot=foreign, date="2026-03-01", title="X", unit_price="100",
        )


def test_field_task_on_retired_pivot_is_rejected():
    client, pivot, _ = _fixtures()
    pivot.status = Pivot.Status.RETIRED
    pivot.save()
    with pytest.raises(ValidationError):
        register_field_task(
            client=client, pivot=pivot, date="2026-03-01", title="X", unit_price="100",
        )


def test_cutting_posts_no_ledger_entry():
    client, _, crop = _fixtures()
    register_cutting(crop=crop, date="2026-04-15", kg_harvested="8200", bales=140)
    assert LedgerEntry.objects.filter(account=client.account).count() == 0
    assert Cutting.objects.filter(crop=crop).count() == 1
    client.account.refresh_from_db()
    assert client.account.balance_cached == Decimal("0")


def test_cutting_on_terminated_crop_is_rejected():
    _, _, crop = _fixtures()
    crop.status = Crop.Status.TERMINATED
    crop.save()
    with pytest.raises(ValidationError):
        register_cutting(crop=crop, date="2026-04-15", kg_harvested="1000")
