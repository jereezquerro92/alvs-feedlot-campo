"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Feedyard services (adr-33-feedyard-operating-loop).

Neither service posts a ledger entry — feedyard plans and measures, it does not
charge (decision 1). Both reject an inactive pen in the SERVICE, not the view
(decision 6); a `LoadingOrder` also rejects an inactive ration. Late data with a
retroactive date is accepted while the pen (and ration) stay active — same posture
as adr-28 for animals.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.feedyard.models import BunkScore, LoadingOrder, Pen, PenPlacement, Ration
from apps.livestock.models import Animal


@transaction.atomic
def register_loading_order(
    *, pen, ration, date, planned_as_fed_kg, notes="", created_by=None
):
    if pen.status != Pen.Status.ACTIVE:
        raise ValidationError(f"El corral no está activo (estado: {pen.status}).")
    if not ration.is_active:
        raise ValidationError("La ración no está activa.")
    return LoadingOrder.objects.create(
        pen=pen,
        ration=ration,
        date=date,
        planned_as_fed_kg=Decimal(planned_as_fed_kg),
        notes=notes,
        created_by=created_by,
    )


@transaction.atomic
def register_bunk_score(*, pen, date, score, notes="", created_by=None):
    if pen.status != Pen.Status.ACTIVE:
        raise ValidationError(f"El corral no está activo (estado: {pen.status}).")
    score = int(score)
    if not 0 <= score <= 4:
        raise ValidationError("El score de comedero debe estar entre 0 y 4.")
    return BunkScore.objects.create(
        pen=pen, date=date, score=score, notes=notes, created_by=created_by
    )


@transaction.atomic
def register_placement(
    *, pen, date, direction, animal=None, lot=None, head_count=None, notes="",
    created_by=None,
):
    """Move an Animal or Lot into/out of a Pen (adr-34). Posts no ledger entry."""
    if pen.status != Pen.Status.ACTIVE:
        raise ValidationError(f"El corral no está activo (estado: {pen.status}).")
    if bool(animal) == bool(lot):
        raise ValidationError("Indicá exactamente uno: `animal` o `lot`.")
    if animal is not None and animal.status != Animal.Status.ACTIVE:
        raise ValidationError(
            f"El animal no está activo (estado: {animal.status}); no se ubica."
        )
    if lot is not None and head_count is None:
        head_count = lot.head_count
    return PenPlacement.objects.create(
        pen=pen,
        animal=animal,
        lot=lot,
        date=date,
        direction=direction,
        head_count=head_count,
        notes=notes,
        created_by=created_by,
    )


def pen_occupancy(*, pen, as_of=None):
    """Current head in a pen = Σ head(in) − Σ head(out), derived (adr-34 decision 1).

    Never a stored number. `as_of` bounds the events by date (inclusive)."""
    qs = PenPlacement.objects.filter(pen=pen)
    if as_of is not None:
        qs = qs.filter(date__lte=as_of)
    head = 0
    for placement in qs:
        moved = placement.head or 0
        head += moved if placement.direction == PenPlacement.Direction.IN else -moved
    return head
