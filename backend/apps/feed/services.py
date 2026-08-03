"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Feed services — deliveries, stock balance, and the ration costing rule.

The costing rule (adr-25 rules 4–5) is the heart of the system:
  - origin = own_stock    -> OUT movement on own stock + a DEBIT ledger entry.
  - origin = client_stock -> OUT against client stock for what is available
    (uncharged); any shortfall is an OUT on own stock + a DEBIT for that
    remainder at unit_price (adr-25 rule 5). Two movements, one debit.
Both origins are always valued for metrics; only the own-stock portion is billed.

FeedingEvent.origin is single-valued. On a client_stock shortfall the event keeps
origin=client_stock (the requested origin); the split lives in the movements and
the ledger debit for the own-stock remainder — not in a second FeedingEvent.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from apps.feed.models import FeedDelivery, FeedingEvent, FeedStockMovement, OwnerKind
from apps.ledger.models import Concept, Direction
from apps.ledger.services import post_entry

ZERO = Decimal("0")


def stock_balance(*, feed_type, owner_kind, client=None):
    """Derived available stock = sum(in) - sum(out) for the given ownership."""
    qs = FeedStockMovement.objects.filter(feed_type=feed_type, owner_kind=owner_kind)
    if owner_kind == OwnerKind.CLIENT:
        qs = qs.filter(client=client)
    totals = {
        row["direction"]: row["total"] or Decimal("0")
        for row in qs.values("direction").annotate(total=Sum("quantity"))
    }
    return totals.get(FeedStockMovement.Direction.IN, Decimal("0")) - totals.get(
        FeedStockMovement.Direction.OUT, Decimal("0")
    )


def _out_movement(*, owner_kind, client, feed_type, quantity, date, source_id):
    FeedStockMovement.objects.create(
        owner_kind=owner_kind,
        client=client if owner_kind == OwnerKind.CLIENT else None,
        feed_type=feed_type,
        direction=FeedStockMovement.Direction.OUT,
        quantity=quantity,
        date=date,
        source_kind="feeding_event",
        source_id=source_id,
    )


def _debit_own_portion(*, client, feed_type, quantity, unit_price, date, source_id, created_by):
    post_entry(
        account=client.account,
        direction=Direction.DEBIT,
        amount=quantity * unit_price,
        concept=Concept.FEEDING,
        date=date,
        source_kind="feeding_event",
        source_id=source_id,
        unit_price=unit_price,
        quantity=quantity,
        description=f"Ración {feed_type.name}",
        created_by=created_by,
    )


@transaction.atomic
def register_delivery(*, client, feed_type, quantity, date, created_by=None):
    quantity = Decimal(quantity)
    if quantity <= 0:
        raise ValidationError("La cantidad debe ser positiva.")
    delivery = FeedDelivery.objects.create(
        client=client, feed_type=feed_type, quantity=quantity, date=date, created_by=created_by
    )
    FeedStockMovement.objects.create(
        owner_kind=OwnerKind.CLIENT,
        client=client,
        feed_type=feed_type,
        direction=FeedStockMovement.Direction.IN,
        quantity=quantity,
        date=date,
        source_kind="feed_delivery",
        source_id=delivery.id,
    )
    return delivery


@transaction.atomic
def register_feeding(*, client, feed_type, quantity, unit_price, origin, date, animal=None, lot=None, pen=None, created_by=None):
    """Record a ration and apply the costing rule (adr-25 rules 4–5).

    `pen` is an optional grouping (adr-33 decision 3): additive, never required,
    and it changes nothing about the costing — the charge still follows origin /
    the shortfall split.
    """
    quantity = Decimal(quantity)
    unit_price = Decimal(unit_price)
    if quantity <= 0:
        raise ValidationError("La cantidad debe ser positiva.")
    if unit_price < 0:
        raise ValidationError("El precio unitario no puede ser negativo.")
    feeding = FeedingEvent.objects.create(
        client=client,
        animal=animal,
        lot=lot,
        pen=pen,
        feed_type=feed_type,
        quantity=quantity,
        unit_price=unit_price,
        origin=origin,
        date=date,
        created_by=created_by,
    )

    if origin == FeedingEvent.Origin.OWN_STOCK:
        _out_movement(
            owner_kind=OwnerKind.OWN,
            client=client,
            feed_type=feed_type,
            quantity=quantity,
            date=date,
            source_id=feeding.id,
        )
        _debit_own_portion(
            client=client,
            feed_type=feed_type,
            quantity=quantity,
            unit_price=unit_price,
            date=date,
            source_id=feeding.id,
            created_by=created_by,
        )
        return feeding

    # client_stock — adr-25 rule 5 shortfall auto-split.
    available = max(
        ZERO,
        stock_balance(feed_type=feed_type, owner_kind=OwnerKind.CLIENT, client=client),
    )
    from_client = min(quantity, available)
    from_own = quantity - from_client

    if from_client > ZERO:
        _out_movement(
            owner_kind=OwnerKind.CLIENT,
            client=client,
            feed_type=feed_type,
            quantity=from_client,
            date=date,
            source_id=feeding.id,
        )

    if from_own > ZERO:
        _out_movement(
            owner_kind=OwnerKind.OWN,
            client=client,
            feed_type=feed_type,
            quantity=from_own,
            date=date,
            source_id=feeding.id,
        )
        _debit_own_portion(
            client=client,
            feed_type=feed_type,
            quantity=from_own,
            unit_price=unit_price,
            date=date,
            source_id=feeding.id,
            created_by=created_by,
        )

    return feeding
