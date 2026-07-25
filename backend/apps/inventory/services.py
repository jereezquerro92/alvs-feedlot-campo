"""Inventory services — the only sanctioned write path for a stock movement.

`register_input_movement` gates an inactive input type and a non-positive quantity
(adr-37 decision 4); a stock that would go negative is NOT blocked — it surfaces as an
inconsistency later (adr-29 posture). `current_stock` derives Σin − Σout; no stored field.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from apps.inventory.models import InputStockMovement, OwnerKind

ZERO = Decimal("0")


@transaction.atomic
def register_input_movement(
    *, input_type, direction, quantity, date, owner_kind=OwnerKind.OWN,
    client=None, unit_price=None, note="", source_kind="", source_id=None,
    created_by=None,
):
    """Record an immutable in/out movement. Posts no ledger entry (adr-37 decision 3)."""
    if not input_type.is_active:
        raise ValidationError("Cannot move stock of an inactive input type.")
    if quantity is None or Decimal(quantity) <= ZERO:
        raise ValidationError("Movement quantity must be positive.")
    if owner_kind == OwnerKind.CLIENT and client is None:
        raise ValidationError("A client-owned movement requires a client.")

    return InputStockMovement.objects.create(
        input_type=input_type,
        direction=direction,
        quantity=quantity,
        date=date,
        owner_kind=owner_kind,
        client=client,
        unit_price=unit_price,
        note=note,
        source_kind=source_kind,
        source_id=source_id,
        created_by=created_by,
    )


def current_stock(*, input_type, owner_kind=OwnerKind.OWN, client=None):
    """Derived stock of an input for one owner = Σ quantity(in) − Σ quantity(out)."""
    rows = InputStockMovement.objects.filter(
        input_type=input_type, owner_kind=owner_kind, client=client
    )

    def _sum(direction):
        return rows.filter(direction=direction).aggregate(t=Sum("quantity"))["t"] or ZERO

    return _sum(InputStockMovement.Direction.IN) - _sum(InputStockMovement.Direction.OUT)
