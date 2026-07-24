"""Crops services (adr-32-multi-rubro-assets).

`register_cutting` records a harvest and posts NO ledger entry (decision 4).
`register_field_task` records labor and always posts a `service` debit through the
generic `(source_kind, source_id)` seam (decisions 3, 5) — `ledger` gains nothing.
The price is snapshotted at creation so later edits never rewrite history (adr-25
rule 3). Both reject a retired pivot in the service, not the view (adr-32 decision 6).
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.crops.models import Crop, Cutting, FieldTask, Pivot
from apps.ledger.models import Concept, Direction
from apps.ledger.services import post_entry


@transaction.atomic
def register_cutting(
    *, crop, date, kg_harvested, bales=None, quality="", notes="", created_by=None
):
    if crop.status != Crop.Status.ACTIVE:
        raise ValidationError(f"El cultivo no está activo (estado: {crop.status}).")
    if crop.pivot.status != Pivot.Status.ACTIVE:
        raise ValidationError("El pivote está dado de baja.")
    return Cutting.objects.create(
        crop=crop,
        date=date,
        kg_harvested=Decimal(kg_harvested),
        bales=bales,
        quality=quality,
        notes=notes,
        created_by=created_by,
    )


@transaction.atomic
def register_field_task(
    *, client, pivot, date, title, unit_price, quantity=Decimal("1"),
    category=FieldTask.Category.OTHER, description="", created_by=None,
):
    if pivot.client_id != client.id:
        raise ValidationError("El pivote no pertenece a este cliente.")
    if pivot.status != Pivot.Status.ACTIVE:
        raise ValidationError(f"El pivote no está activo (estado: {pivot.status}).")

    quantity = Decimal(quantity)
    unit_price = Decimal(unit_price)

    task = FieldTask.objects.create(
        client=client,
        pivot=pivot,
        date=date,
        title=title,
        category=category,
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
        source_kind="field_task",
        source_id=task.id,
        unit_price=unit_price,
        quantity=quantity,
        description=f"Tarea {title}",
        created_by=created_by,
    )

    return task
