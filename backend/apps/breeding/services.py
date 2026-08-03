"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Breeding services — the only sanctioned write path for reproductive events.

The single ledger write is in `register_service`: an ai/iatf Service on a
boarding client posts a `service` debit for the insemination fee via the generic
(source_kind="breeding_service", source_id) pair (adr-46 decision 6). Every other
event posts none (decision 1). A service decrements a genetics semen/embryo
movement `out` (decision 7); a live individual calving creates the calf Animal
(decision 4). Business rules are validated here, the single write point (decision 7).
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.dateparse import parse_date

from apps.clients.models import Client
from apps.ledger.models import Concept, Direction
from apps.ledger.services import post_entry
from apps.genetics.models import (
    Direction as MoveDir,
    EmbryoMovement,
    EmbryoReason,
    SemenMovement,
    SemenReason,
)
from apps.genetics.services import current_embryo_stock, current_semen_stock
from apps.livestock.models import Animal, Category, Lot
from apps.breeding.models import (
    Calving,
    CalvingOutcome,
    Method,
    PregnancyCheck,
    Service,
    Weaning,
)

ZERO = Decimal("0")
ONE = Decimal("1")


def _as_date(value):
    """Normalize an ISO date string to a `date` at the write boundary, so a
    returned in-memory event exposes a real date for derived arithmetic (e.g.
    PregnancyCheck.estimated_calving_date) before any DB reload coerces it."""
    if isinstance(value, str):
        parsed = parse_date(value)
        if parsed is None:
            raise ValidationError(f"Invalid date: {value!r}")
        return parsed
    return value


def _resolve_target(animal, lot):
    """Exactly one of animal/lot, active, and its client (adr-26 rule 3)."""
    if bool(animal) == bool(lot):
        raise ValidationError("A breeding event targets exactly one Animal XOR one Lot.")
    if animal is not None:
        if animal.status != Animal.Status.ACTIVE:
            raise ValidationError("Cannot register a breeding event on a non-active animal.")
        return animal.client
    if lot.status != Lot.Status.ACTIVE:
        raise ValidationError("Cannot register a breeding event on a closed lot.")
    return lot.client


@transaction.atomic
def register_service(
    *, animal=None, lot=None, date, method, sire=None, semen_batch=None,
    embryo_batch=None, protocol=None, service_price=None, note="", created_by=None,
):
    """Record a service and consume genetics stock (decision 7).

    ai/iatf require a semen batch with stock; embryo_transfer requires an embryo
    batch with stock. Only ai/iatf on a boarding client, with a positive
    service_price, posts a `service` debit for the insemination fee (decision 6) —
    an honest cut: no price, no fabricated charge.
    """
    client = _resolve_target(animal, lot)
    date = _as_date(date)

    if method in (Method.AI, Method.IATF):
        if semen_batch is None:
            raise ValidationError("An ai/iatf service requires a semen batch.")
        if not semen_batch.is_active:
            raise ValidationError("Cannot use an inactive semen batch.")
        if current_semen_stock(semen_batch=semen_batch) < ONE:
            raise ValidationError("Insufficient straw stock for this service.")
    if method == Method.IATF and protocol is not None and not protocol.is_active:
        raise ValidationError("Cannot use an inactive IATF protocol.")
    if method == Method.EMBRYO_TRANSFER:
        if embryo_batch is None:
            raise ValidationError("An embryo transfer requires an embryo batch.")
        if not embryo_batch.is_active:
            raise ValidationError("Cannot use an inactive embryo batch.")
        if current_embryo_stock(embryo_batch=embryo_batch) < ONE:
            raise ValidationError("Insufficient embryo stock for this transfer.")

    service = Service.objects.create(
        animal=animal,
        lot=lot,
        client=client,
        date=date,
        method=method,
        sire=sire,
        semen_batch=semen_batch,
        embryo_batch=embryo_batch,
        protocol=protocol,
        service_price=(Decimal(service_price) if service_price is not None else None),
        note=note,
        created_by=created_by,
    )

    if method in (Method.AI, Method.IATF):
        SemenMovement.objects.create(
            semen_batch=semen_batch,
            direction=MoveDir.OUT,
            straws=ONE,
            reason=SemenReason.INSEMINATION,
            date=date,
            source_kind="breeding_service",
            source_id=service.id,
            created_by=created_by,
        )
    elif method == Method.EMBRYO_TRANSFER:
        EmbryoMovement.objects.create(
            embryo_batch=embryo_batch,
            direction=MoveDir.OUT,
            quantity=ONE,
            reason=EmbryoReason.TRANSFER,
            date=date,
            source_kind="breeding_service",
            source_id=service.id,
            created_by=created_by,
        )

    # The one ledger write: insemination fee, boarding client only (decision 6).
    price = service.service_price
    if (
        method in (Method.AI, Method.IATF)
        and client.kind == Client.Kind.BOARDING
        and price is not None
        and price > ZERO
    ):
        post_entry(
            account=client.account,
            direction=Direction.DEBIT,
            amount=price,
            concept=Concept.SERVICE,
            date=date,
            source_kind="breeding_service",
            source_id=service.id,
            unit_price=price,
            quantity=ONE,
            description=f"Servicio de inseminación ({method})",
            created_by=created_by,
        )

    return service


@transaction.atomic
def register_pregnancy_check(
    *, animal=None, lot=None, date, method, result, gestation_days=None,
    service=None, note="", created_by=None,
):
    """Record a pregnancy diagnosis. Posts no ledger entry (decision 1)."""
    client = _resolve_target(animal, lot)
    date = _as_date(date)
    return PregnancyCheck.objects.create(
        animal=animal,
        lot=lot,
        client=client,
        date=date,
        method=method,
        result=result,
        gestation_days=gestation_days,
        service=service,
        note=note,
        created_by=created_by,
    )


@transaction.atomic
def register_calving(
    *, animal=None, lot=None, date, outcome, calving_ease="normal", calf_sex="",
    calf_weight=None, births_count=None, service=None, note="", created_by=None,
):
    """Record a calving. A live individual calving creates the calf Animal
    (decision 4). Posts no ledger entry (decision 1)."""
    client = _resolve_target(animal, lot)
    date = _as_date(date)

    calf = None
    if animal is not None and outcome == CalvingOutcome.LIVE:
        base = f"{animal.ear_tag}-C"
        seq = Animal.objects.filter(client=client, ear_tag__startswith=base).count() + 1
        calf = Animal.objects.create(
            client=client,
            ear_tag=f"{base}{seq}",
            category=Category.CALF,
            sex=calf_sex,
            entry_date=date,
            entry_weight=(Decimal(calf_weight) if calf_weight is not None else None),
            current_weight=(Decimal(calf_weight) if calf_weight is not None else None),
        )

    return Calving.objects.create(
        animal=animal,
        lot=lot,
        client=client,
        date=date,
        outcome=outcome,
        calving_ease=calving_ease,
        calf_sex=calf_sex,
        calf_weight=(Decimal(calf_weight) if calf_weight is not None else None),
        births_count=births_count,
        service=service,
        calf=calf,
        note=note,
        created_by=created_by,
    )


@transaction.atomic
def register_weaning(
    *, animal=None, lot=None, date, weaning_weight, purpose="undecided",
    note="", created_by=None,
):
    """Record a weaning. Posts no ledger entry (decision 1)."""
    client = _resolve_target(animal, lot)
    date = _as_date(date)
    return Weaning.objects.create(
        animal=animal,
        lot=lot,
        client=client,
        date=date,
        weaning_weight=Decimal(weaning_weight),
        purpose=purpose,
        note=note,
        created_by=created_by,
    )
