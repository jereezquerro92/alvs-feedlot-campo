"""Machinery services (adr-32-multi-rubro-assets).

`register_maintenance` records a service/repair and always posts a `service` debit
through the generic `(source_kind, source_id)` seam (decisions 3, 5). Price is
snapshotted at creation (adr-25 rule 3); a retired machine is rejected in the
service, not the view (adr-32 decision 6).
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.ledger.models import Concept, Direction
from apps.ledger.services import post_entry
from apps.machinery.models import Machine, MaintenanceEvent


@transaction.atomic
def register_maintenance(
    *, client, machine, date, title, unit_price, quantity=Decimal("1"),
    kind=MaintenanceEvent.Kind.PREVENTIVE, hours=None, description="", created_by=None,
):
    if machine.client_id != client.id:
        raise ValidationError("La máquina no pertenece a este cliente.")
    if machine.status != Machine.Status.ACTIVE:
        raise ValidationError(f"La máquina no está activa (estado: {machine.status}).")

    quantity = Decimal(quantity)
    unit_price = Decimal(unit_price)

    event = MaintenanceEvent.objects.create(
        client=client,
        machine=machine,
        date=date,
        title=title,
        kind=kind,
        hours=hours,
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
        source_kind="maintenance_event",
        source_id=event.id,
        unit_price=unit_price,
        quantity=quantity,
        description=f"Mantenimiento {title}",
        created_by=created_by,
    )

    return event
