"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Traceability services — the only sanctioned write path for a DT-e or a caravana.

`register_transit` gates inactive/equal establishments, a non-positive head count and a
duplicate `dte_number` (adr-38 decision 3). `register_caravana` gates a non-active animal
and a duplicate `official_number` (decision 4). Neither posts a ledger entry (decision 2).
"""

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.traceability.models import Caravana, Establishment, TransitDocument


@transaction.atomic
def register_transit(
    *, dte_number, origin, destination, date, head_count,
    category=TransitDocument.Category.MIXED, total_weight=None, lot=None,
    note="", created_by=None,
):
    """Record an immutable DT-e transit. Posts no ledger entry (adr-38 decision 2)."""
    if not isinstance(origin, Establishment) or not isinstance(destination, Establishment):
        raise ValidationError("Origin and destination must be establishments.")
    if not origin.is_active or not destination.is_active:
        raise ValidationError("Both origin and destination establishments must be active.")
    if origin.pk == destination.pk:
        raise ValidationError("Origin and destination must differ.")
    if head_count is None or int(head_count) <= 0:
        raise ValidationError("Head count must be positive.")
    if TransitDocument.objects.filter(dte_number=dte_number).exists():
        raise ValidationError("A transit document with this DT-e number already exists.")

    return TransitDocument.objects.create(
        dte_number=dte_number,
        origin=origin,
        destination=destination,
        date=date,
        category=category,
        head_count=head_count,
        total_weight=total_weight,
        lot=lot,
        note=note,
        created_by=created_by,
    )


@transaction.atomic
def register_caravana(*, official_number, animal, assigned_date, note="", created_by=None):
    """Bind a unique official caravan number to an active animal (adr-38 decision 4)."""
    if animal.status != animal.Status.ACTIVE:
        raise ValidationError("Only an active animal can be caravanned.")
    if Caravana.objects.filter(official_number=official_number).exists():
        raise ValidationError("A caravana with this official number already exists.")

    return Caravana.objects.create(
        official_number=official_number,
        animal=animal,
        assigned_date=assigned_date,
        note=note,
        created_by=created_by,
    )
