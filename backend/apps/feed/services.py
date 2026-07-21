"""Feed services — deliveries, stock balance, and the ration costing rule.

The costing rule (adr-25 rule 4) is the heart of the system:
  - origin = own_stock    -> OUT movement on own stock + a DEBIT ledger entry.
  - origin = client_stock -> OUT movement on the client's stock, NO charge.
Both are always valued for metrics; only own stock is billed. Phase 1 does not
auto-split a client-stock shortfall (that stays an open decision) — the origin
determines the behavior wholesale.
"""

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.feed.models import FeedDelivery, FeedingEvent, FeedStockMovement, OwnerKind
from apps.ledger.models import Concept, Direction
from apps.ledger.services import post_entry


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


@transaction.atomic
def register_delivery(*, client, feed_type, quantity, date, created_by=None):
    delivery = FeedDelivery.objects.create(
        client=client, feed_type=feed_type, quantity=Decimal(quantity), date=date, created_by=created_by
    )
    FeedStockMovement.objects.create(
        owner_kind=OwnerKind.CLIENT,
        client=client,
        feed_type=feed_type,
        direction=FeedStockMovement.Direction.IN,
        quantity=Decimal(quantity),
        date=date,
        source_kind="feed_delivery",
        source_id=delivery.id,
    )
    return delivery


@transaction.atomic
def register_feeding(*, client, feed_type, quantity, unit_price, origin, date, animal=None, lot=None, created_by=None):
    """Record a ration and apply the costing rule (adr-25 rule 4)."""
    quantity = Decimal(quantity)
    unit_price = Decimal(unit_price)
    feeding = FeedingEvent.objects.create(
        client=client,
        animal=animal,
        lot=lot,
        feed_type=feed_type,
        quantity=quantity,
        unit_price=unit_price,
        origin=origin,
        date=date,
        created_by=created_by,
    )

    owner_kind = (
        OwnerKind.CLIENT if origin == FeedingEvent.Origin.CLIENT_STOCK else OwnerKind.OWN
    )
    FeedStockMovement.objects.create(
        owner_kind=owner_kind,
        client=client if owner_kind == OwnerKind.CLIENT else None,
        feed_type=feed_type,
        direction=FeedStockMovement.Direction.OUT,
        quantity=quantity,
        date=date,
        source_kind="feeding_event",
        source_id=feeding.id,
    )

    # Only own feed is billed to the client's account.
    if origin == FeedingEvent.Origin.OWN_STOCK:
        post_entry(
            account=client.account,
            direction=Direction.DEBIT,
            amount=quantity * unit_price,
            concept=Concept.FEEDING,
            date=date,
            source_kind="feeding_event",
            source_id=feeding.id,
            unit_price=unit_price,
            quantity=quantity,
            description=f"Ración {feed_type.name}",
            created_by=created_by,
        )

    return feeding
