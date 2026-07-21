"""Intake services — create cattle individually or as a lot (adr-26 rule 1)."""

from decimal import Decimal

from django.db import transaction

from apps.livestock.models import Animal, Intake, Lot


@transaction.atomic
def create_individual_intake(*, client, date, animals):
    """`animals`: list of dicts {ear_tag, category, sex?, entry_weight?}."""
    intake = Intake.objects.create(
        client=client, date=date, mode=Intake.Mode.INDIVIDUAL, head_count=len(animals)
    )
    created = []
    for a in animals:
        created.append(
            Animal.objects.create(
                client=client,
                ear_tag=a["ear_tag"],
                category=a["category"],
                sex=a.get("sex", ""),
                entry_date=date,
                entry_weight=a.get("entry_weight"),
                current_weight=a.get("entry_weight"),
            )
        )
    return intake, created


@transaction.atomic
def create_lot_intake(*, client, date, code, head_count, total_weight):
    lot = Lot.objects.create(
        client=client,
        code=code,
        mode=Lot.Mode.ANONYMOUS,
        head_count=head_count,
        total_weight=Decimal(total_weight),
    )
    intake = Intake.objects.create(
        client=client,
        date=date,
        mode=Intake.Mode.LOT,
        head_count=head_count,
        total_weight=Decimal(total_weight),
        lot=lot,
    )
    return intake, lot


# --- Phase 2: animal lifecycle ------------------------------------------------
#
# Weighings, deaths and exits. None of them post to the ledger: feed and health
# are what get billed, and feed already consumed by an animal that later died
# stays billed (docs/feedlot/11-plan-de-fases.md, decision 1).

from django.core.exceptions import ValidationError

from apps.livestock.models import Death, Exit, Weighing


def _resolve_target(animal, lot):
    if bool(animal) == bool(lot):
        raise ValidationError("Indicar exactamente uno: animal o lote.")
    return animal or lot


def _assert_active(target):
    if isinstance(target, Animal):
        if target.status != Animal.Status.ACTIVE:
            raise ValidationError(f"El animal no está activo (estado: {target.status}).")
    elif target.status != Lot.Status.ACTIVE:
        raise ValidationError(f"El lote no está activo (estado: {target.status}).")


def _entry_date(target):
    """Earliest date the target existed, to reject events dated before it."""
    if isinstance(target, Animal):
        return target.entry_date
    first = Intake.objects.filter(lot=target).order_by("date").values_list("date", flat=True).first()
    return first


@transaction.atomic
def register_weighing(
    *, animal=None, lot=None, weight, date, head_count=None, method=Weighing.Method.SCALE,
    notes="", created_by=None,
):
    target = _resolve_target(animal, lot)
    _assert_active(target)

    entry_date = _entry_date(target)
    if entry_date and str(date) < str(entry_date):
        raise ValidationError("El pesaje no puede ser anterior al ingreso.")

    if lot is not None and head_count is None:
        head_count = lot.head_count

    weighing = Weighing.objects.create(
        animal=animal, lot=lot, weight=Decimal(weight), date=date,
        head_count=head_count, method=method, notes=notes, created_by=created_by,
    )

    if animal is not None:
        animal.current_weight = Decimal(weight)
        animal.save(update_fields=["current_weight"])
    else:
        lot.total_weight = Decimal(weight)
        lot.save(update_fields=["total_weight"])

    return weighing


def growth_series(*, animal=None, lot=None):
    """Weighings plus the average daily gain between consecutive readings.

    For lots the comparison is per head, never on the total: an intake or a death
    between two readings moves the total for reasons that have nothing to do with
    growth. When the head count changed between two readings the period is
    reported as not calculable rather than guessed (decision 2).
    """
    target = _resolve_target(animal, lot)
    qs = Weighing.objects.filter(animal=animal) if animal else Weighing.objects.filter(lot=lot)
    readings = list(qs.order_by("date", "id"))

    series = []
    previous = None
    for reading in readings:
        adg = None
        reason = ""
        if previous is not None:
            days = (reading.date - previous.date).days
            if days <= 0:
                reason = "same_date"
            elif lot is not None and previous.head_count != reading.head_count:
                reason = "head_count_changed"
            else:
                adg = (reading.weight_per_head - previous.weight_per_head) / Decimal(days)
        series.append(
            {
                "weighing": reading.id,
                "date": reading.date,
                "weight": reading.weight,
                "head_count": reading.head_count,
                "weight_per_head": reading.weight_per_head,
                "adg": adg,
                "not_calculable": reason,
            }
        )
        previous = reading
    return series


@transaction.atomic
def register_death(
    *, animal=None, lot=None, date, cause=Death.Cause.UNKNOWN, cause_detail="",
    head_count=None, weight=None, created_by=None,
):
    target = _resolve_target(animal, lot)
    _assert_active(target)

    if lot is not None:
        head_count = int(head_count or 1)
        if head_count > lot.head_count:
            raise ValidationError(
                f"No se pueden dar de baja {head_count} cabezas: el lote tiene {lot.head_count}."
            )

    death = Death.objects.create(
        animal=animal, lot=lot, date=date, cause=cause, cause_detail=cause_detail,
        head_count=head_count, weight=Decimal(weight) if weight is not None else None,
        created_by=created_by,
    )

    if animal is not None:
        animal.status = Animal.Status.DEAD
        animal.save(update_fields=["status"])
    else:
        _reduce_lot(lot, head_count, weight)

    return death


@transaction.atomic
def register_exit(
    *, animal=None, lot=None, date, kind=Exit.Kind.SALE, destination="",
    head_count=None, weight=None, sale_price_per_kg=None, created_by=None,
):
    target = _resolve_target(animal, lot)
    _assert_active(target)

    if lot is not None:
        head_count = int(head_count or lot.head_count)
        if head_count > lot.head_count:
            raise ValidationError(
                f"No se pueden egresar {head_count} cabezas: el lote tiene {lot.head_count}."
            )

    exit_event = Exit.objects.create(
        animal=animal, lot=lot, date=date, kind=kind, destination=destination,
        head_count=head_count, weight=Decimal(weight) if weight is not None else None,
        sale_price_per_kg=Decimal(sale_price_per_kg) if sale_price_per_kg is not None else None,
        created_by=created_by,
    )

    if animal is not None:
        animal.status = Animal.Status.SOLD if kind == Exit.Kind.SALE else Animal.Status.EXITED
        animal.save(update_fields=["status"])
    else:
        _reduce_lot(lot, head_count, weight)

    return exit_event


def _reduce_lot(lot, head_count, weight):
    """Subtract head and kilos; close the lot when it empties out."""
    head_count = int(head_count or 0)
    lot.head_count = max(lot.head_count - head_count, 0)
    if weight is not None:
        lot.total_weight = max(lot.total_weight - Decimal(weight), Decimal("0"))
    if lot.head_count == 0:
        lot.status = Lot.Status.CLOSED
    lot.save(update_fields=["head_count", "total_weight", "status"])
