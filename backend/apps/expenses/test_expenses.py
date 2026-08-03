"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Extra expenses (gastos): the field manager's "carga de deudas" as immutable
events that post a `service` debit through the ledger's generic seam
([[adr-44-field-operational-roles]] decision 6, [[adr-24-feedlot-domain]] rule 4).
Never a manual ledger debit, never a mutation of an existing entry (adr-25 rule 1)."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.clients.models import Client
from apps.expenses.models import ExpenseEvent
from apps.expenses.services import register_expense
from apps.ledger.models import Concept, Direction, LedgerEntry
from apps.livestock.models import Lot

pytestmark = pytest.mark.django_db


def _client(kind=Client.Kind.BOARDING, name="El Ombú"):
    return Client.objects.create(name=name, kind=kind)


def test_labor_expense_charges_the_account_as_a_service():
    client = _client()
    expense = register_expense(
        client=client, date="2026-03-01", title="Mano de obra corrales",
        category=ExpenseEvent.Category.LABOR, unit_price="1500", quantity="8",
    )
    entry = LedgerEntry.objects.get(account=client.account)
    assert entry.direction == Direction.DEBIT
    assert entry.concept == Concept.SERVICE
    assert entry.amount == Decimal("12000.00")
    assert entry.source_kind == "expense_event"
    assert entry.source_id == expense.id
    assert entry.unit_price == Decimal("1500.0000")
    assert entry.quantity == Decimal("8.000")
    client.account.refresh_from_db()
    assert client.account.balance_cached == Decimal("12000.00")


def test_fuel_expense_snapshots_litres_and_price_and_keeps_fuel_kind():
    client = _client()
    expense = register_expense(
        client=client, date="2026-03-02", title="Gasoil tractor",
        category=ExpenseEvent.Category.FUEL, unit_price="850", quantity="120",
        fuel_kind="diesel",
    )
    assert expense.fuel_kind == "diesel"
    assert expense.total_cost == Decimal("102000.0000")
    entry = LedgerEntry.objects.get(account=client.account)
    assert entry.amount == Decimal("102000.00")
    assert entry.concept == Concept.SERVICE


def test_expense_can_be_attributed_to_a_lot_of_the_client():
    client = _client()
    lot = Lot.objects.create(client=client, code="L1", head_count=50)
    expense = register_expense(
        client=client, date="2026-03-03", title="Maquinaria",
        category=ExpenseEvent.Category.MACHINERY, unit_price="4000", quantity="1",
        lot=lot,
    )
    assert expense.lot_id == lot.id


def test_expense_lot_defaults_to_none_meaning_whole_client():
    client = _client()
    expense = register_expense(
        client=client, date="2026-03-03", title="Gasto general",
        unit_price="1000", quantity="1",
    )
    assert expense.lot_id is None


def test_expense_on_another_clients_lot_is_rejected():
    client = _client()
    other = _client(name="La Otra")
    foreign_lot = Lot.objects.create(client=other, code="LX", head_count=10)
    with pytest.raises(ValidationError):
        register_expense(
            client=client, date="2026-03-01", title="X", unit_price="100",
            lot=foreign_lot,
        )


def test_expense_rejects_non_positive_quantity():
    client = _client()
    with pytest.raises(ValidationError):
        register_expense(
            client=client, date="2026-03-01", title="X", unit_price="100",
            quantity="0",
        )


def test_expense_rejects_negative_unit_price():
    client = _client()
    with pytest.raises(ValidationError):
        register_expense(
            client=client, date="2026-03-01", title="X", unit_price="-5",
            quantity="1",
        )


def test_expense_never_mutates_an_existing_entry_it_appends():
    client = _client()
    register_expense(
        client=client, date="2026-03-01", title="Uno", unit_price="100", quantity="1",
    )
    register_expense(
        client=client, date="2026-03-02", title="Dos", unit_price="200", quantity="1",
    )
    entries = LedgerEntry.objects.filter(account=client.account)
    assert entries.count() == 2
    client.account.refresh_from_db()
    assert client.account.balance_cached == Decimal("300.00")
