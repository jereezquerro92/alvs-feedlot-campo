"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Genetics services — the only sanctioned write path for inventory and sales.

Movements and flushes post NO ledger entry (adr-47 decision 6). The sole ledger
write is `register_semen_sale`: a `sale` credit to the own account plus an `out`
movement, in one transaction (decision 4). Stock is derived Σin − Σout (decision 2);
no stored field.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from apps.clients.models import Client
from apps.ledger.models import Concept, Direction
from apps.ledger.services import post_entry
from apps.genetics.models import (
    Direction as MoveDir,
    EmbryoBatch,
    EmbryoMovement,
    EmbryoReason,
    SemenMovement,
    SemenReason,
    SemenSale,
)

ZERO = Decimal("0")


def current_semen_stock(*, semen_batch):
    """Derived straws of a batch = Σ straws(in) − Σ straws(out) (decision 2)."""
    rows = SemenMovement.objects.filter(semen_batch=semen_batch)

    def _sum(direction):
        return rows.filter(direction=direction).aggregate(t=Sum("straws"))["t"] or ZERO

    return _sum(MoveDir.IN) - _sum(MoveDir.OUT)


def current_embryo_stock(*, embryo_batch):
    """Derived embryos of a batch = Σ quantity(in) − Σ quantity(out) (decision 2)."""
    rows = EmbryoMovement.objects.filter(embryo_batch=embryo_batch)

    def _sum(direction):
        return rows.filter(direction=direction).aggregate(t=Sum("quantity"))["t"] or ZERO

    return _sum(MoveDir.IN) - _sum(MoveDir.OUT)


@transaction.atomic
def register_semen_movement(
    *, semen_batch, direction, straws, reason, date,
    source_kind="", source_id=None, note="", created_by=None,
):
    """Record an immutable straw movement. Posts no ledger entry (adr-47 decision 6)."""
    if not semen_batch.is_active:
        raise ValidationError("Cannot move straws of an inactive semen batch.")
    if straws is None or Decimal(straws) <= ZERO:
        raise ValidationError("Movement straws must be positive.")

    return SemenMovement.objects.create(
        semen_batch=semen_batch,
        direction=direction,
        straws=Decimal(straws),
        reason=reason,
        date=date,
        source_kind=source_kind,
        source_id=source_id,
        note=note,
        created_by=created_by,
    )


@transaction.atomic
def register_semen_sale(
    *, semen_batch, straws, unit_price, date,
    buyer_name="", buyer_client=None, note="", created_by=None,
):
    """Sell straws: a `sale` credit to the own account + an `out` movement (decision 4).

    Validates in the service (decision 7): a positive price, sufficient stock, and an
    existing own account to credit. The credit lowers the own account's balance, making
    the genetic margin legible (adr-43 decision 3 precedent). Snapshots unit_price ×
    straws of the day (adr-25 regla 3).
    """
    straws = Decimal(straws)
    if straws <= ZERO:
        raise ValidationError("Sale straws must be positive.")
    if unit_price is None or Decimal(unit_price) <= ZERO:
        raise ValidationError("Sale price must be positive.")
    if current_semen_stock(semen_batch=semen_batch) < straws:
        raise ValidationError("Insufficient straw stock for this sale.")

    own = Client.objects.filter(kind=Client.Kind.OWN).first()
    if own is None:
        raise ValidationError("No own account (Client kind=own) to credit the sale.")

    unit_price = Decimal(unit_price)
    sale = SemenSale.objects.create(
        semen_batch=semen_batch,
        date=date,
        straws=straws,
        unit_price=unit_price,
        buyer_name=buyer_name,
        buyer_client=buyer_client,
        note=note,
        created_by=created_by,
    )

    post_entry(
        account=own.account,
        direction=Direction.CREDIT,
        amount=straws * unit_price,
        concept=Concept.SALE,
        date=date,
        source_kind="semen_sale",
        source_id=sale.id,
        unit_price=unit_price,
        quantity=straws,
        description=f"Venta de semen {semen_batch.batch_code}",
        created_by=created_by,
    )

    SemenMovement.objects.create(
        semen_batch=semen_batch,
        direction=MoveDir.OUT,
        straws=straws,
        reason=SemenReason.SALE,
        date=date,
        source_kind="semen_sale",
        source_id=sale.id,
        created_by=created_by,
    )

    return sale


@transaction.atomic
def register_embryo_movement(
    *, embryo_batch, direction, quantity, reason, date,
    source_kind="", source_id=None, note="", created_by=None,
):
    """Record an immutable embryo movement. Posts no ledger entry (adr-47 decision 6)."""
    if not embryo_batch.is_active:
        raise ValidationError("Cannot move embryos of an inactive batch.")
    if quantity is None or Decimal(quantity) <= ZERO:
        raise ValidationError("Movement quantity must be positive.")

    return EmbryoMovement.objects.create(
        embryo_batch=embryo_batch,
        direction=direction,
        quantity=Decimal(quantity),
        reason=reason,
        date=date,
        source_kind=source_kind,
        source_id=source_id,
        note=note,
        created_by=created_by,
    )


@transaction.atomic
def register_embryo_flush(
    *, donor, date, embryos_collected, sire=None, grade="",
    embryo_batch=None, note="", created_by=None,
):
    """A donor collection: create/update an EmbryoBatch + post an `in` movement (decision 5).

    Produces inventory; posts no ledger entry. When no target batch is given, a new
    EmbryoBatch is created for the donor.
    """
    embryos_collected = Decimal(embryos_collected)
    if embryos_collected <= ZERO:
        raise ValidationError("Embryos collected must be positive.")

    from apps.genetics.models import EmbryoFlush

    if embryo_batch is None:
        embryo_batch = EmbryoBatch.objects.create(
            donor=donor, sire=sire, grade=grade, flush_date=date,
        )

    flush = EmbryoFlush.objects.create(
        donor=donor, sire=sire, date=date,
        embryos_collected=embryos_collected, grade=grade, note=note,
        created_by=created_by,
    )

    EmbryoMovement.objects.create(
        embryo_batch=embryo_batch,
        direction=MoveDir.IN,
        quantity=embryos_collected,
        reason=EmbryoReason.COLLECTION,
        date=date,
        source_kind="embryo_flush",
        source_id=flush.id,
        created_by=created_by,
    )

    return flush
