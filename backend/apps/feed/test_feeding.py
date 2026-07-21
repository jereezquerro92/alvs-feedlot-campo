"""The costing rule is the heart of Phase 1 (adr-25 rule 4)."""

from decimal import Decimal

import pytest

from apps.clients.models import Client
from apps.feed.models import FeedingEvent, FeedStockMovement, FeedType, OwnerKind
from apps.feed.services import register_delivery, register_feeding, stock_balance
from apps.ledger.models import Concept, Direction, LedgerEntry
from apps.livestock.models import Lot

pytestmark = pytest.mark.django_db


def _fixtures():
    client = Client.objects.create(name="La Esperanza", kind=Client.Kind.BOARDING)
    feed = FeedType.objects.create(name="Maíz molido")
    lot = Lot.objects.create(client=client, code="L-07", head_count=46, total_weight=Decimal("21850"))
    return client, feed, lot


def test_own_stock_feeding_charges_the_account():
    client, feed, lot = _fixtures()
    register_feeding(
        client=client, feed_type=feed, quantity="1000", unit_price="285",
        origin=FeedingEvent.Origin.OWN_STOCK, date="2026-07-21", lot=lot,
    )
    entries = LedgerEntry.objects.filter(account=client.account)
    assert entries.count() == 1
    entry = entries.get()
    assert entry.direction == Direction.DEBIT
    assert entry.concept == Concept.FEEDING
    assert entry.amount == Decimal("285000.00")
    assert entry.source_kind == "feeding_event"
    client.account.refresh_from_db()
    assert client.account.balance_cached == Decimal("285000.00")


def test_client_stock_feeding_does_not_charge():
    client, feed, lot = _fixtures()
    register_delivery(client=client, feed_type=feed, quantity="5000", date="2026-07-20")
    register_feeding(
        client=client, feed_type=feed, quantity="1000", unit_price="285",
        origin=FeedingEvent.Origin.CLIENT_STOCK, date="2026-07-21", lot=lot,
    )
    assert LedgerEntry.objects.filter(account=client.account).count() == 0
    client.account.refresh_from_db()
    assert client.account.balance_cached == Decimal("0.00")
    # Client stock decremented: 5000 in - 1000 out = 4000
    assert stock_balance(feed_type=feed, owner_kind=OwnerKind.CLIENT, client=client) == Decimal("4000.00")


def test_own_stock_goes_negative_but_is_tracked():
    client, feed, lot = _fixtures()
    register_feeding(
        client=client, feed_type=feed, quantity="1000", unit_price="285",
        origin=FeedingEvent.Origin.OWN_STOCK, date="2026-07-21", lot=lot,
    )
    # One OUT movement on own stock; balance -1000 (no purchase loaded yet).
    assert stock_balance(feed_type=feed, owner_kind=OwnerKind.OWN) == Decimal("-1000.00")
    assert FeedStockMovement.objects.filter(direction="out").count() == 1


def test_feeding_requires_exactly_one_target():
    from apps.feed.serializers import FeedingEventSerializer

    client, feed, lot = _fixtures()
    base = {"client": client.id, "feed_type": feed.id, "quantity": "10",
            "unit_price": "1", "origin": "own_stock", "date": "2026-07-21"}
    # Neither target set.
    assert not FeedingEventSerializer(data=base).is_valid()
    # Both targets set.
    from apps.livestock.models import Animal

    animal = Animal.objects.create(client=client, ear_tag="A1", category="cow", entry_date="2026-07-01")
    assert not FeedingEventSerializer(data={**base, "animal": animal.id, "lot": lot.id}).is_valid()
    # Exactly one target set.
    assert FeedingEventSerializer(data={**base, "lot": lot.id}).is_valid()
