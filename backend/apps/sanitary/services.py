"""Health application service — always posts a debit (Phase 2).

Unlike feeding, there is no origin split: health products are always supplied by
the feedlot, so every application is charged. The price is snapshotted from the
catalogue at creation time so later catalogue edits never rewrite history.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.ledger.models import Concept, Direction
from apps.ledger.services import post_entry
from apps.livestock.models import Animal, Lot
from apps.sanitary.models import HealthEvent


@transaction.atomic
def register_health_event(
    *, client, product, quantity, date, animal=None, lot=None, head_count=None,
    unit_price=None, applied_by="", notes="", created_by=None,
):
    if bool(animal) == bool(lot):
        raise ValidationError("Indicar exactamente uno: animal o lote.")

    target = animal or lot
    if target.client_id != client.id:
        raise ValidationError("El animal o lote no pertenece a este cliente.")

    status_active = (
        Animal.Status.ACTIVE if animal is not None else Lot.Status.ACTIVE
    )
    if target.status != status_active:
        raise ValidationError(f"El destino no está activo (estado: {target.status}).")

    quantity = Decimal(quantity)
    # Snapshot: the catalogue can change tomorrow, this entry cannot.
    unit_price = Decimal(unit_price) if unit_price is not None else product.unit_price

    event = HealthEvent.objects.create(
        client=client, animal=animal, lot=lot, product=product, quantity=quantity,
        head_count=head_count, unit_price=unit_price, date=date,
        applied_by=applied_by, notes=notes, created_by=created_by,
    )

    post_entry(
        account=client.account,
        direction=Direction.DEBIT,
        amount=quantity * unit_price,
        concept=Concept.HEALTH,
        date=date,
        source_kind="health_event",
        source_id=event.id,
        unit_price=unit_price,
        quantity=quantity,
        description=f"Sanidad {product.name}",
        created_by=created_by,
    )

    return event
