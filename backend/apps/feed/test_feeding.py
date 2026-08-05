"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""The costing rule is the heart of Phase 1 (adr-25 rule 4)."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

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


def test_client_stock_shortfall_splits_and_charges_remainder():
    """adr-25 rule 5: available from client (uncharged), remainder own + debit."""
    client, feed, lot = _fixtures()
    register_delivery(client=client, feed_type=feed, quantity="300", date="2026-07-20")
    feeding = register_feeding(
        client=client, feed_type=feed, quantity="1000", unit_price="100",
        origin=FeedingEvent.Origin.CLIENT_STOCK, date="2026-07-21", lot=lot,
    )

    assert feeding.origin == FeedingEvent.Origin.CLIENT_STOCK
    assert feeding.quantity == Decimal("1000")

    client_outs = FeedStockMovement.objects.filter(
        owner_kind=OwnerKind.CLIENT, direction="out", source_id=feeding.id,
    )
    own_outs = FeedStockMovement.objects.filter(
        owner_kind=OwnerKind.OWN, direction="out", source_id=feeding.id,
    )
    assert client_outs.count() == 1
    assert client_outs.get().quantity == Decimal("300.00")
    assert own_outs.count() == 1
    assert own_outs.get().quantity == Decimal("700.00")

    entries = LedgerEntry.objects.filter(account=client.account)
    assert entries.count() == 1
    entry = entries.get()
    assert entry.direction == Direction.DEBIT
    assert entry.quantity == Decimal("700.00")
    assert entry.amount == Decimal("70000.00")
    assert entry.source_kind == "feeding_event"
    assert entry.source_id == feeding.id

    assert stock_balance(feed_type=feed, owner_kind=OwnerKind.CLIENT, client=client) == Decimal("0.00")
    assert stock_balance(feed_type=feed, owner_kind=OwnerKind.OWN) == Decimal("-700.00")


def test_client_stock_exact_balance_no_charge():
    """When quantity equals available client stock: one client OUT, no debit."""
    client, feed, lot = _fixtures()
    register_delivery(client=client, feed_type=feed, quantity="1000", date="2026-07-20")
    feeding = register_feeding(
        client=client, feed_type=feed, quantity="1000", unit_price="100",
        origin=FeedingEvent.Origin.CLIENT_STOCK, date="2026-07-21", lot=lot,
    )

    assert FeedStockMovement.objects.filter(owner_kind=OwnerKind.CLIENT, direction="out").count() == 1
    assert FeedStockMovement.objects.filter(owner_kind=OwnerKind.OWN, direction="out").count() == 0
    assert LedgerEntry.objects.filter(account=client.account).count() == 0
    assert stock_balance(feed_type=feed, owner_kind=OwnerKind.CLIENT, client=client) == Decimal("0.00")
    assert feeding.origin == FeedingEvent.Origin.CLIENT_STOCK


def test_client_stock_zero_available_full_charge_from_own():
    """No client delivery: full quantity from own stock + debit; no client OUT."""
    client, feed, lot = _fixtures()
    feeding = register_feeding(
        client=client, feed_type=feed, quantity="1000", unit_price="100",
        origin=FeedingEvent.Origin.CLIENT_STOCK, date="2026-07-21", lot=lot,
    )

    assert feeding.origin == FeedingEvent.Origin.CLIENT_STOCK
    assert FeedStockMovement.objects.filter(owner_kind=OwnerKind.CLIENT, direction="out").count() == 0
    own_outs = FeedStockMovement.objects.filter(owner_kind=OwnerKind.OWN, direction="out")
    assert own_outs.count() == 1
    assert own_outs.get().quantity == Decimal("1000.00")

    entry = LedgerEntry.objects.get(account=client.account)
    assert entry.quantity == Decimal("1000.00")
    assert entry.amount == Decimal("100000.00")
    assert entry.source_id == feeding.id
    assert stock_balance(feed_type=feed, owner_kind=OwnerKind.OWN) == Decimal("-1000.00")


@pytest.mark.parametrize("quantity", ["0", "-10"])
def test_register_delivery_rejects_non_positive_quantity(quantity):
    client, feed, _ = _fixtures()
    with pytest.raises(ValidationError):
        register_delivery(client=client, feed_type=feed, quantity=quantity, date="2026-07-20")
    assert FeedStockMovement.objects.count() == 0


@pytest.mark.parametrize("quantity", ["0", "-10"])
def test_register_feeding_rejects_non_positive_quantity(quantity):
    client, feed, lot = _fixtures()
    with pytest.raises(ValidationError):
        register_feeding(
            client=client, feed_type=feed, quantity=quantity, unit_price="285",
            origin=FeedingEvent.Origin.OWN_STOCK, date="2026-07-21", lot=lot,
        )
    assert FeedingEvent.objects.count() == 0
    assert LedgerEntry.objects.filter(account=client.account).count() == 0


def test_register_feeding_rejects_negative_unit_price():
    client, feed, lot = _fixtures()
    with pytest.raises(ValidationError):
        register_feeding(
            client=client, feed_type=feed, quantity="100", unit_price="-1",
            origin=FeedingEvent.Origin.OWN_STOCK, date="2026-07-21", lot=lot,
        )
    assert FeedingEvent.objects.count() == 0
    assert LedgerEntry.objects.filter(account=client.account).count() == 0


def test_register_feeding_rejects_inactive_target():
    client, feed, lot = _fixtures()
    lot.status = "closed"
    lot.save()
    with pytest.raises(ValidationError, match="inactive"):
        register_feeding(
            client=client, feed_type=feed, quantity="100", unit_price="285",
            origin=FeedingEvent.Origin.OWN_STOCK, date="2026-07-21", lot=lot,
        )


def test_register_feeding_rejects_wrong_client_target():
    client, feed, lot = _fixtures()
    other_client = Client.objects.create(name="Client B", tax_id="30-77777777-7")
    with pytest.raises(ValidationError, match="belong"):
        register_feeding(
            client=other_client, feed_type=feed, quantity="100", unit_price="285",
            origin=FeedingEvent.Origin.OWN_STOCK, date="2026-07-21", lot=lot,
        )
