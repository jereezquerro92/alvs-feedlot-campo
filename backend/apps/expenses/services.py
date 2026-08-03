"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Expenses service (adr-44 decision 6, adr-49 rule 4).

`register_expense` records an extra charge and ALWAYS posts a `service` debit
through the ledger's generic `(source_kind, source_id)` seam — the in-doctrine
"carga de deudas": an event that bills the account, never a manual ledger debit
and never a mutation of an existing entry (adr-25 rule 1). The price is snapshotted
at creation so a later edit never rewrites history (adr-25 rule 3). Business rules
live here (the single write point), not in the view (same posture as adr-32)."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.expenses.models import ExpenseEvent
from apps.ledger.models import Concept, Direction
from apps.ledger.services import post_entry


@transaction.atomic
def register_expense(
    *, client, date, title, unit_price, quantity=Decimal("1"),
    category=ExpenseEvent.Category.OTHER, lot=None, fuel_kind="",
    description="", created_by=None,
):
    if lot is not None and lot.client_id != client.id:
        raise ValidationError("El lote no pertenece a este cliente.")

    quantity = Decimal(quantity)
    unit_price = Decimal(unit_price)
    if quantity <= 0:
        raise ValidationError("La cantidad debe ser positiva.")
    if unit_price < 0:
        raise ValidationError("El precio unitario no puede ser negativo.")

    expense = ExpenseEvent.objects.create(
        client=client,
        date=date,
        title=title,
        category=category,
        lot=lot,
        fuel_kind=fuel_kind,
        unit_price=unit_price,
        quantity=quantity,
        description=description,
        created_by=created_by,
    )

    post_entry(
        account=client.account,
        direction=Direction.DEBIT,
        amount=quantity * unit_price,
        concept=Concept.SERVICE,
        date=date,
        source_kind="expense_event",
        source_id=expense.id,
        unit_price=unit_price,
        quantity=quantity,
        description=f"Gasto {title}",
        created_by=created_by,
    )

    return expense
