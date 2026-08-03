"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Intake services — create cattle individually or as a lot (adr-26 rule 1)."""

from decimal import Decimal

from django.core.exceptions import ValidationError
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
    """Create a fresh anonymous lot and its opening intake.

    The lot `code` is unique per client (task #20): a friendly ValidationError is
    raised before the write so the caller gets a clean message, not a DB
    IntegrityError leaking out of the UniqueConstraint.
    """
    if Lot.objects.filter(client=client, code=code).exists():
        raise ValidationError(f"El cliente ya tiene un lote con el código «{code}».")

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


@transaction.atomic
def add_to_lot_intake(*, client, date, lot, head_count, total_weight):
    """Add an intake to an EXISTING lot, growing its event-maintained counters.

    ADR-26 rule 1 sanctions `lot` mode as "creates OR updates a Lot": adding head
    and kilos to a lot that already exists is a new Intake event, and the lot's
    counters are moved only by that event (rule 4), never hand-edited. The lot must
    belong to `client` and still be active.
    """
    if lot.client_id != client.id:
        raise ValidationError("El lote pertenece a otro cliente.")
    if lot.status != Lot.Status.ACTIVE:
        raise ValidationError(f"El lote no está activo (estado: {lot.status}).")

    added_head = int(head_count)
    added_weight = Decimal(total_weight)

    intake = Intake.objects.create(
        client=client,
        date=date,
        mode=Intake.Mode.LOT,
        head_count=added_head,
        total_weight=added_weight,
        lot=lot,
    )

    lot.head_count = lot.head_count + added_head
    lot.total_weight = lot.total_weight + added_weight
    lot.save(update_fields=["head_count", "total_weight"])

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
    elif head_count == lot.head_count:
        # Partial samples record the reading but must not overwrite the lot
        # counter — only a full-lot weighing corrects total_weight (#18 / #59).
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

    entry_date = _entry_date(target)
    if entry_date and str(date) < str(entry_date):
        raise ValidationError("La baja no puede ser anterior al ingreso.")

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
    head_count=None, weight=None, sale_price_per_kg=None, commission_pct=None,
    created_by=None,
):
    target = _resolve_target(animal, lot)
    _assert_active(target)

    entry_date = _entry_date(target)
    if entry_date and str(date) < str(entry_date):
        raise ValidationError("El egreso no puede ser anterior al ingreso.")

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
        engorde_commission_pct=(
            Decimal(commission_pct) if commission_pct is not None else None
        ),
        created_by=created_by,
    )

    if animal is not None:
        animal.status = Animal.Status.SOLD if kind == Exit.Kind.SALE else Animal.Status.EXITED
        animal.save(update_fields=["status"])
    else:
        _reduce_lot(lot, head_count, weight)

    _settle_sale(exit_event, animal=animal, lot=lot, created_by=created_by)

    return exit_event


def _settle_sale(exit_event, *, animal, lot, created_by):
    """Post the sale settlement for a `kind=sale` exit (adr-43).

    Boarding cattle (`Client.kind=boarding`): the client sells; the feedlot charges
    an engorde commission, a `service` DEBIT of
    `(pct/100) × kilos_gained × sale_price_per_kg`. Own cattle (`Client.kind=own`):
    the sale is the feedlot's; a `sale` CREDIT of `weight × sale_price_per_kg` on the
    own account, offsetting the accumulated costs so the net reads as margin.

    Honest cut (adr-29 rule 2): when an input is missing — no price, no measurable
    gain (boarding), no commission percent (boarding), or no weight (own) — nothing
    is posted. A fabricated ledger entry is worse than a fabricated metric: it moves
    a real balance. Deaths and non-sale exits never reach here (adr-28 decision 3).

    Lazy imports break the livestock↔metrics / livestock↔ledger cycles.
    """
    if exit_event.kind != Exit.Kind.SALE:
        return None

    from apps.clients.models import Client
    from apps.ledger.models import Concept, Direction
    from apps.ledger.services import post_entry

    price = exit_event.sale_price_per_kg
    if price is None or price <= 0:
        return None

    target = animal or lot
    client = target.client
    account = client.account

    if client.kind == Client.Kind.OWN:
        weight = exit_event.weight
        if weight is None or weight <= 0:
            return None
        produced = weight * price
        return post_entry(
            account=account,
            direction=Direction.CREDIT,
            amount=produced,
            concept=Concept.SALE,
            date=exit_event.date,
            source_kind="exit",
            source_id=exit_event.id,
            unit_price=price,
            quantity=weight,
            description="Venta hacienda propia",
            created_by=created_by,
        )

    # Boarding: engorde commission on measured kilos gained.
    pct = exit_event.engorde_commission_pct
    if pct is None or pct <= 0:
        return None

    from apps.metrics.services import target_kilos_gained

    gained_info = target_kilos_gained(animal=animal, lot=lot)
    if gained_info["segments_measured"] == 0:
        return None
    gained = gained_info["kilos_gained"]
    if gained <= 0:
        return None

    commission = (pct / Decimal("100")) * gained * price
    return post_entry(
        account=account,
        direction=Direction.DEBIT,
        amount=commission,
        concept=Concept.SERVICE,
        date=exit_event.date,
        source_kind="exit",
        source_id=exit_event.id,
        unit_price=price,
        quantity=gained,
        description=f"Comisión de engorde {pct}% s/{gained} kg",
        created_by=created_by,
    )


def _reduce_lot(lot, head_count, weight):
    """Subtract head and kilos; close the lot when it empties out.

    Weight-less reductions take a proportional share of `total_weight` so the
    remaining avg kg/head stays consistent (#32 / #59). When `weight` is given
    it is authoritative (same as before).
    """
    head_count = int(head_count or 0)
    prior_head = lot.head_count
    if weight is not None:
        weight_delta = Decimal(weight)
    elif prior_head > 0 and head_count > 0:
        weight_delta = lot.total_weight * Decimal(head_count) / Decimal(prior_head)
    else:
        weight_delta = Decimal("0")

    lot.head_count = max(prior_head - head_count, 0)
    lot.total_weight = max(lot.total_weight - weight_delta, Decimal("0"))
    if lot.head_count == 0:
        lot.status = Lot.Status.CLOSED
    lot.save(update_fields=["head_count", "total_weight", "status"])
