"""Phase 2: health applications always bill the client."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.clients.models import Client
from apps.ledger.models import Concept, Direction, LedgerEntry
from apps.livestock.models import Animal
from apps.sanitary.models import HealthProduct
from apps.sanitary.services import register_health_event

pytestmark = pytest.mark.django_db


def _fixtures():
    client = Client.objects.create(name="La Esperanza", kind=Client.Kind.BOARDING)
    product = HealthProduct.objects.create(
        name="Aftosa", kind=HealthProduct.Kind.VACCINE, unit_price=Decimal("1500")
    )
    animal = Animal.objects.create(
        client=client, ear_tag="A-001", category="steer", entry_date="2026-01-10"
    )
    return client, product, animal


def test_health_event_charges_the_account():
    client, product, animal = _fixtures()
    register_health_event(
        client=client, product=product, animal=animal, quantity="2", date="2026-03-01"
    )
    entry = LedgerEntry.objects.get(account=client.account)
    assert entry.direction == Direction.DEBIT
    assert entry.concept == Concept.HEALTH
    assert entry.amount == Decimal("3000.00")
    assert entry.source_kind == "health_event"
    client.account.refresh_from_db()
    assert client.account.balance_cached == Decimal("3000.00")


def test_unit_price_is_snapshotted_at_application_time():
    client, product, animal = _fixtures()
    event = register_health_event(
        client=client, product=product, animal=animal, quantity="1", date="2026-03-01"
    )
    product.unit_price = Decimal("9999")
    product.save()
    event.refresh_from_db()
    assert event.unit_price == Decimal("1500.0000")
    assert LedgerEntry.objects.get(account=client.account).amount == Decimal("1500.00")


def test_application_on_another_clients_animal_is_rejected():
    client, product, _ = _fixtures()
    other = Client.objects.create(name="El Ombú", kind=Client.Kind.BOARDING)
    foreign = Animal.objects.create(
        client=other, ear_tag="B-001", category="steer", entry_date="2026-01-10"
    )
    with pytest.raises(ValidationError):
        register_health_event(
            client=client, product=product, animal=foreign, quantity="1", date="2026-03-01"
        )


def test_application_requires_exactly_one_target():
    client, product, _ = _fixtures()
    with pytest.raises(ValidationError):
        register_health_event(client=client, product=product, quantity="1", date="2026-03-01")


def test_health_and_feeding_accumulate_in_the_same_balance():
    from apps.feed.models import FeedingEvent, FeedType
    from apps.feed.services import register_feeding
    from apps.livestock.models import Lot

    client, product, animal = _fixtures()
    lot = Lot.objects.create(client=client, code="L-01", head_count=10, total_weight=Decimal("3200"))
    register_feeding(
        client=client, feed_type=FeedType.objects.create(name="Maíz"), quantity="100",
        unit_price="285", origin=FeedingEvent.Origin.OWN_STOCK, date="2026-03-01", lot=lot,
    )
    register_health_event(
        client=client, product=product, animal=animal, quantity="2", date="2026-03-01"
    )
    client.account.refresh_from_db()
    assert client.account.balance_cached == Decimal("31500.00")  # 28500 + 3000
