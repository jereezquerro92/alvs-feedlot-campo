"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Phase 4b (metrics): per-pen feed conversion, the honest cut (adr-42).

Kilos gained are attributed to a pen ONLY for weighing segments a target spent
entirely inside one continuous stay in that pen, derived from PenPlacement events.
Everything ambiguous returns null + a reason rather than a fabricated number
(adr-29 rule 2). Read-only: it posts no ledger entry.
"""

from decimal import Decimal

import pytest

from apps.clients.models import Client
from apps.feed.models import FeedType
from apps.feed.services import register_feeding
from apps.feedyard.models import Pen, PenPlacement
from apps.feedyard.services import register_placement
from apps.ledger.models import LedgerEntry
from apps.livestock.models import Animal, Lot
from apps.livestock.services import register_weighing
from apps.metrics.services import pen_closeout, pen_conversion

pytestmark = pytest.mark.django_db

IN = PenPlacement.Direction.IN
OUT = PenPlacement.Direction.OUT


def _client():
    return Client.objects.create(name="El Corral", kind=Client.Kind.BOARDING)


def _feed():
    return FeedType.objects.create(name="Silaje")


def _animal(client, tag="A-1", entry="2026-07-01"):
    return Animal.objects.create(
        client=client, ear_tag=tag, category="steer", entry_date=entry
    )


# --- clean single-stay attribution -------------------------------------------

def test_clean_single_stay_gives_a_conversion():
    """An animal that stayed in one pen for the whole weighing interval attributes
    its gain to that pen; conversion = kg fed ÷ kg gained (adr-42 decision 2)."""
    client = _client()
    pen = Pen.objects.create(code="C-01", name="Corral 1")
    animal = _animal(client)

    register_placement(pen=pen, date="2026-07-01", direction=IN, animal=animal)
    register_weighing(animal=animal, weight="100", date="2026-07-01")
    register_weighing(animal=animal, weight="130", date="2026-07-31")
    register_feeding(
        client=client, feed_type=_feed(), quantity="60", unit_price="100",
        origin="own_stock", date="2026-07-15", animal=animal, pen=pen,
    )

    result = pen_conversion(pen=pen, start="2026-07-01", end="2026-07-31")
    assert result["kilos_gained"] == Decimal("30")
    assert result["kilos_fed"] == Decimal("60.00")
    assert result["conversion"] == Decimal("2")
    assert result["not_calculable"] == ""
    assert result["segments_attributed"] == 1
    assert result["segments_unattributed"] == 0


def test_conversion_reads_no_ledger():
    """The metric is read-only — computing it posts nothing (adr-42 decision 5)."""
    client = _client()
    pen = Pen.objects.create(code="C-02")
    animal = _animal(client)
    register_placement(pen=pen, date="2026-07-01", direction=IN, animal=animal)
    register_weighing(animal=animal, weight="100", date="2026-07-01")
    register_weighing(animal=animal, weight="130", date="2026-07-31")

    before = LedgerEntry.objects.count()
    pen_conversion(pen=pen, start="2026-07-01", end="2026-07-31")
    assert LedgerEntry.objects.count() == before


# --- ambiguous attribution is refused ----------------------------------------

def test_mid_segment_pen_change_is_not_attributed():
    """Moving pens between two weighings makes the gain unattributable — the growth
    was split across pens in a way the data does not record (adr-42 decision 2)."""
    client = _client()
    pen_a = Pen.objects.create(code="C-0A")
    pen_b = Pen.objects.create(code="C-0B")
    animal = _animal(client)

    register_placement(pen=pen_a, date="2026-07-01", direction=IN, animal=animal)
    register_placement(pen=pen_a, date="2026-07-15", direction=OUT, animal=animal)
    register_placement(pen=pen_b, date="2026-07-15", direction=IN, animal=animal)
    register_weighing(animal=animal, weight="100", date="2026-07-01")
    register_weighing(animal=animal, weight="130", date="2026-07-31")
    register_feeding(
        client=client, feed_type=_feed(), quantity="60", unit_price="100",
        origin="own_stock", date="2026-07-10", animal=animal, pen=pen_a,
    )

    result = pen_conversion(pen=pen_a, start="2026-07-01", end="2026-07-31")
    assert result["conversion"] is None
    assert result["not_calculable"] == "no_attributable_growth"
    assert result["segments_attributed"] == 0
    assert result["segments_unattributed"] == 1


def test_feed_without_attributable_growth_is_null():
    """Feed to a pen whose targets have no attributable segment yields null, never a
    fabricated conversion (adr-42 decision 4)."""
    client = _client()
    pen = Pen.objects.create(code="C-03")
    animal = _animal(client)
    register_placement(pen=pen, date="2026-07-01", direction=IN, animal=animal)
    register_weighing(animal=animal, weight="100", date="2026-07-01")  # one reading only
    register_feeding(
        client=client, feed_type=_feed(), quantity="60", unit_price="100",
        origin="own_stock", date="2026-07-15", animal=animal, pen=pen,
    )

    result = pen_conversion(pen=pen, start="2026-07-01", end="2026-07-31")
    assert result["conversion"] is None
    assert result["not_calculable"] == "no_attributable_growth"


def test_attributable_growth_without_feed_is_null():
    """Gain pinned to the pen but no feed recorded there → null with a distinct reason,
    not a misleading zero conversion (adr-42 decision 4)."""
    client = _client()
    pen = Pen.objects.create(code="C-04")
    animal = _animal(client)
    register_placement(pen=pen, date="2026-07-01", direction=IN, animal=animal)
    register_weighing(animal=animal, weight="100", date="2026-07-01")
    register_weighing(animal=animal, weight="130", date="2026-07-31")

    result = pen_conversion(pen=pen, start="2026-07-01", end="2026-07-31")
    assert result["segments_attributed"] == 1
    assert result["kilos_fed"] == Decimal("0")
    assert result["conversion"] is None
    assert result["not_calculable"] == "no_feed_recorded"


# --- lots --------------------------------------------------------------------

def test_lot_gain_is_attributed_per_head():
    """A lot that stayed in the pen attributes per-head gain × head count (adr-42
    decision 2, matching kilos_gained's per-head rule)."""
    client = _client()
    pen = Pen.objects.create(code="C-05")
    lot = Lot.objects.create(
        client=client, code="L-5", head_count=10, total_weight=Decimal("1000")
    )
    from apps.livestock.models import Intake
    Intake.objects.create(
        client=client, date="2026-07-01", mode=Intake.Mode.LOT,
        head_count=10, total_weight=Decimal("1000"), lot=lot,
    )

    register_placement(pen=pen, date="2026-07-01", direction=IN, lot=lot, head_count=10)
    register_weighing(lot=lot, weight="1000", date="2026-07-01", head_count=10)  # 100/head
    register_weighing(lot=lot, weight="1200", date="2026-07-31", head_count=10)  # 120/head
    register_feeding(
        client=client, feed_type=_feed(), quantity="400", unit_price="100",
        origin="own_stock", date="2026-07-15", lot=lot, pen=pen,
    )

    result = pen_conversion(pen=pen, start="2026-07-01", end="2026-07-31")
    # 20 kg/head × 10 head = 200 kg gained; 400 fed → conversion 2.
    assert result["kilos_gained"] == Decimal("200")
    assert result["conversion"] == Decimal("2")


def test_lot_head_count_change_is_skipped_not_unattributed():
    """A non-calculable ADG segment (lot head count changed, adr-28 rule 2) is skipped,
    not counted as unattributed (adr-42 decision 3)."""
    client = _client()
    pen = Pen.objects.create(code="C-06")
    lot = Lot.objects.create(
        client=client, code="L-6", head_count=10, total_weight=Decimal("1000")
    )
    from apps.livestock.models import Intake
    Intake.objects.create(
        client=client, date="2026-07-01", mode=Intake.Mode.LOT,
        head_count=10, total_weight=Decimal("1000"), lot=lot,
    )
    register_placement(pen=pen, date="2026-07-01", direction=IN, lot=lot, head_count=10)
    register_weighing(lot=lot, weight="1000", date="2026-07-01", head_count=10)
    register_weighing(lot=lot, weight="1080", date="2026-07-31", head_count=9)  # head changed

    result = pen_conversion(pen=pen, start="2026-07-01", end="2026-07-31")
    assert result["segments_skipped"] == 1
    assert result["segments_attributed"] == 0
    assert result["not_calculable"] == "no_attributable_growth"


# --- closeout composes both halves -------------------------------------------

def test_pen_closeout_carries_occupancy_and_conversion():
    """The full closeout composes the affirmable occupancy half with the honest
    conversion half (adr-42 decision, consequences)."""
    client = _client()
    pen = Pen.objects.create(code="C-07")
    animal = _animal(client)
    register_placement(pen=pen, date="2026-07-01", direction=IN, animal=animal)
    register_weighing(animal=animal, weight="100", date="2026-07-01")
    register_weighing(animal=animal, weight="130", date="2026-07-31")
    register_feeding(
        client=client, feed_type=_feed(), quantity="60", unit_price="100",
        origin="own_stock", date="2026-07-15", animal=animal, pen=pen,
    )

    closeout = pen_closeout(pen=pen, start="2026-07-01", end="2026-07-31")
    assert closeout["code"] == "C-07"
    assert closeout["current_head"] == 1
    assert closeout["conversion"]["conversion"] == Decimal("2")
