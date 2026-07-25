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

from apps.feedyard.models import BunkScore, LoadingOrder, Pen, Ration


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
