"""Phase 6 (machinery): maintenance events bill the client as a `service` through
the ledger's generic seam (adr-32-multi-rubro-assets)."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.clients.models import Client
from apps.ledger.models import Concept, Direction, LedgerEntry
from apps.machinery.models import Machine, MaintenanceEvent
from apps.machinery.services import register_maintenance

pytestmark = pytest.mark.django_db


def _fixtures():
    client = Client.objects.create(name="Feedlot Propio", kind=Client.Kind.OWN)
    machine = Machine.objects.create(
        client=client, name="Tractor JD 6110", category=Machine.Category.TRACTOR
    )
    return client, machine


def test_maintenance_charges_the_account_as_a_service():
    client, machine = _fixtures()
    event = register_maintenance(
        client=client, machine=machine, date="2026-03-01", title="Cambio de aceite",
        unit_price="45000", quantity="1", kind=MaintenanceEvent.Kind.PREVENTIVE,
    )
    entry = LedgerEntry.objects.get(account=client.account)
    assert entry.direction == Direction.DEBIT
    assert entry.concept == Concept.SERVICE
    assert entry.amount == Decimal("45000.00")
    assert entry.source_kind == "maintenance_event"
    assert entry.source_id == event.id
    client.account.refresh_from_db()
    assert client.account.balance_cached == Decimal("45000.00")


def test_maintenance_unit_price_is_snapshotted():
    client, machine = _fixtures()
    event = register_maintenance(
        client=client, machine=machine, date="2026-03-01", title="Filtros",
        unit_price="12000", quantity="2",
    )
    assert event.unit_price == Decimal("12000.0000")
    assert event.total_cost == Decimal("24000.0000")


def test_maintenance_on_another_clients_machine_is_rejected():
    client, _ = _fixtures()
    other = Client.objects.create(name="Contratista", kind=Client.Kind.BOARDING)
    foreign = Machine.objects.create(client=other, name="Ajena")
    with pytest.raises(ValidationError):
        register_maintenance(
            client=client, machine=foreign, date="2026-03-01", title="X", unit_price="100",
        )


def test_maintenance_on_retired_machine_is_rejected():
    client, machine = _fixtures()
    machine.status = Machine.Status.RETIRED
    machine.save()
    with pytest.raises(ValidationError):
        register_maintenance(
            client=client, machine=machine, date="2026-03-01", title="X", unit_price="100",
        )
