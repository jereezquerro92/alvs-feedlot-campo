"""Phase 7b (feedyard): cattle placement into pens is an immutable event; occupancy
is derived, never stored (adr-34). Posts no ledger entry."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.clients.models import Client
from apps.feedyard.models import Pen, PenPlacement
from apps.feedyard.services import pen_occupancy, register_placement
from apps.ledger.models import LedgerEntry
from apps.livestock.models import Animal, Lot
from apps.metrics.services import pen_occupancy_report

pytestmark = pytest.mark.django_db


def _fixtures():
    client = Client.objects.create(name="El Corral", kind=Client.Kind.BOARDING)
    pen = Pen.objects.create(code="C-09", name="Corral 9", capacity_head=200)
    lot = Lot.objects.create(
        client=client, code="L-9", head_count=80, total_weight=Decimal("36000")
    )
    animal = Animal.objects.create(
        client=client, ear_tag="A-9", category="steer", entry_date="2026-07-01"
    )
    return client, pen, lot, animal


def test_placement_posts_no_ledger_entry():
    client, pen, lot, _ = _fixtures()
    placement = register_placement(
        pen=pen, date="2026-07-10", direction=PenPlacement.Direction.IN, lot=lot
    )
    assert isinstance(placement, PenPlacement)
    assert LedgerEntry.objects.filter(account=client.account).count() == 0


def test_lot_placement_defaults_head_count_to_lot_size():
    _, pen, lot, _ = _fixtures()
    placement = register_placement(
        pen=pen, date="2026-07-10", direction=PenPlacement.Direction.IN, lot=lot
    )
    assert placement.head_count == 80
    assert placement.head == 80


def test_animal_placement_counts_one_head():
    _, pen, _, animal = _fixtures()
    placement = register_placement(
        pen=pen, date="2026-07-10", direction=PenPlacement.Direction.IN, animal=animal
    )
    assert placement.head == 1
    assert pen_occupancy(pen=pen) == 1


def test_occupancy_is_in_minus_out():
    _, pen, lot, _ = _fixtures()
    register_placement(
        pen=pen, date="2026-07-10", direction=PenPlacement.Direction.IN, lot=lot
    )  # +80
    register_placement(
        pen=pen, date="2026-07-20", direction=PenPlacement.Direction.OUT, lot=lot,
        head_count=30,
    )  # -30
    assert pen_occupancy(pen=pen) == 50


def test_occupancy_respects_as_of_bound():
    _, pen, lot, _ = _fixtures()
    register_placement(
        pen=pen, date="2026-07-10", direction=PenPlacement.Direction.IN, lot=lot,
        head_count=80,
    )
    register_placement(
        pen=pen, date="2026-07-25", direction=PenPlacement.Direction.OUT, lot=lot,
        head_count=80,
    )
    assert pen_occupancy(pen=pen, as_of="2026-07-20") == 80
    assert pen_occupancy(pen=pen, as_of="2026-07-25") == 0


def test_placement_requires_exactly_one_target():
    _, pen, lot, animal = _fixtures()
    with pytest.raises(ValidationError):
        register_placement(
            pen=pen, date="2026-07-10", direction=PenPlacement.Direction.IN,
            animal=animal, lot=lot,
        )
    with pytest.raises(ValidationError):
        register_placement(
            pen=pen, date="2026-07-10", direction=PenPlacement.Direction.IN
        )


def test_placement_on_inactive_pen_is_rejected():
    _, pen, lot, _ = _fixtures()
    pen.status = Pen.Status.INACTIVE
    pen.save()
    with pytest.raises(ValidationError):
        register_placement(
            pen=pen, date="2026-07-10", direction=PenPlacement.Direction.IN, lot=lot
        )


def test_dead_animal_cannot_be_placed():
    _, pen, _, animal = _fixtures()
    animal.status = Animal.Status.DEAD
    animal.save()
    with pytest.raises(ValidationError):
        register_placement(
            pen=pen, date="2026-07-10", direction=PenPlacement.Direction.IN, animal=animal
        )


def test_xor_constraint_is_enforced_at_the_database():
    _, pen, lot, animal = _fixtures()
    with pytest.raises(IntegrityError):
        PenPlacement.objects.create(
            pen=pen, date="2026-07-10", direction=PenPlacement.Direction.IN,
            animal=animal, lot=lot,
        )


def test_pen_occupancy_report_summarises_movements_and_feed():
    client, pen, lot, _ = _fixtures()
    from apps.feed.models import FeedType
    from apps.feed.services import register_feeding

    feed = FeedType.objects.create(name="Silaje")
    register_placement(
        pen=pen, date="2026-07-10", direction=PenPlacement.Direction.IN, lot=lot,
        head_count=80,
    )
    register_placement(
        pen=pen, date="2026-07-20", direction=PenPlacement.Direction.OUT, lot=lot,
        head_count=20,
    )
    register_feeding(
        client=client, feed_type=feed, quantity="1200", unit_price="100",
        origin="own_stock", date="2026-07-15", lot=lot, pen=pen,
    )
    report = pen_occupancy_report(pen=pen, start="2026-07-01", end="2026-07-31")
    assert report["code"] == "C-09"
    assert report["current_head"] == 60
    assert report["head_moved_in"] == 80
    assert report["head_moved_out"] == 20
    assert report["kilos_fed"] == Decimal("1200.00")
