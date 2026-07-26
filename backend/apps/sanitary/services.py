"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Health application service — always posts a debit (Phase 2).

Unlike feeding, there is no origin split: health products are always supplied by
the feedlot, so every application is charged. The price is snapshotted from the
catalogue at creation time so later catalogue edits never rewrite history.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.ledger.models import Concept, Direction
from apps.ledger.services import post_entry
from apps.livestock.models import Animal, Lot
from apps.sanitary.models import HealthEvent, PlanEnrollment


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


def _as_date(value):
    """Accept a date or an ISO string; the service is the single write point."""
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


@transaction.atomic
def enroll_in_plan(
    *, plan, client, start_date, animal=None, lot=None, notes="", created_by=None
):
    """Bind a target (animal XOR lot) to a plan on a start date (adr-40 decision 1).

    Validates in the service (adr-40 decision 5): active plan, exactly one target, the
    target belongs to the client and is active. Posts NO ledger entry — a plan is
    intent, not an applied input; billing stays with HealthEvent (adr-40 decision 4).
    """
    if bool(animal) == bool(lot):
        raise ValidationError("Indicar exactamente uno: animal o lote.")

    if not plan.is_active:
        raise ValidationError("El plan sanitario no está activo.")

    target = animal or lot
    if target.client_id != client.id:
        raise ValidationError("El animal o lote no pertenece a este cliente.")

    status_active = Animal.Status.ACTIVE if animal is not None else Lot.Status.ACTIVE
    if target.status != status_active:
        raise ValidationError(f"El destino no está activo (estado: {target.status}).")

    return PlanEnrollment.objects.create(
        plan=plan, client=client, animal=animal, lot=lot,
        start_date=_as_date(start_date), notes=notes, created_by=created_by,
    )


def plan_schedule_for_client(client, *, as_of=None):
    """Derive the sanitary calendar for a client (adr-40 decision 3).

    Pure read: for every enrollment whose target is still active, each plan item's due
    date is `start_date + day_offset`. A dose is `applied` when a HealthEvent exists for
    the same target and product dated on/after the enrollment start; else `pending` when
    already due (`due_date <= as_of`), else `upcoming`. Nothing is stored; no enrollments
    → empty list (never a fabricated state, adr-29 posture).
    """
    as_of = _as_date(as_of) if as_of else date.today()

    enrollments = (
        PlanEnrollment.objects.filter(client=client)
        .select_related("plan", "animal", "lot")
        .prefetch_related("plan__items__product")
    )

    items = []
    for enr in enrollments:
        target = enr.animal or enr.lot
        if target is None:
            continue
        status_active = (
            Animal.Status.ACTIVE if enr.animal is not None else Lot.Status.ACTIVE
        )
        if target.status != status_active:
            continue

        target_label = enr.animal.ear_tag if enr.animal is not None else enr.lot.code
        target_filter = (
            {"animal_id": enr.animal_id} if enr.animal_id else {"lot_id": enr.lot_id}
        )

        # Sequential attribution: N applications of a product satisfy the N
        # earliest-due doses of that product, never every future dose (adr-40
        # decision 3). Count the applications per product once, then consume them
        # in offset order — the plan items already sort by day_offset.
        applications_left = {}
        for product_id in {item.product_id for item in enr.plan.items.all()}:
            applications_left[product_id] = HealthEvent.objects.filter(
                product_id=product_id, date__gte=enr.start_date, **target_filter
            ).count()

        for item in enr.plan.items.all():
            due_date = enr.start_date + timedelta(days=item.day_offset)
            if applications_left.get(item.product_id, 0) > 0:
                applications_left[item.product_id] -= 1
                status = "applied"
            elif due_date <= as_of:
                status = "pending"
            else:
                status = "upcoming"

            items.append({
                "enrollment": enr.id,
                "plan": enr.plan_id,
                "plan_name": enr.plan.name,
                "animal": enr.animal_id,
                "lot": enr.lot_id,
                "target_label": target_label,
                "product": item.product_id,
                "product_name": item.product.name,
                "day_offset": item.day_offset,
                "due_date": due_date.isoformat(),
                "dose": str(item.dose),
                "status": status,
            })

    # Sort by due date so the caller reads the calendar in order.
    items.sort(key=lambda row: (row["due_date"], row["product_name"]))
    pending_count = sum(1 for row in items if row["status"] == "pending")

    return {
        "client": client.id,
        "as_of": as_of.isoformat(),
        "items": items,
        "pending_count": pending_count,
    }
