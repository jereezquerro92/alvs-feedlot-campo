"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Phase 7 (feedyard): the pen operating loop plans and measures but NEVER charges
(adr-33). Billing stays in `feed`. The executed ration groups by pen additively,
which the cost-side pen summary reads (adr-33 decisions 1, 3, 7)."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.clients.models import Client
from apps.feed.models import FeedingEvent, FeedType
from apps.feed.services import register_feeding
from apps.feedyard.models import BunkScore, LoadingOrder, Pen, Ration, RationLine
from apps.feedyard.services import register_bunk_score, register_loading_order
from apps.ledger.models import LedgerEntry
from apps.livestock.models import Lot
from apps.metrics.services import pen_cost_summary

pytestmark = pytest.mark.django_db


def _fixtures():
    client = Client.objects.create(name="La Carga", kind=Client.Kind.BOARDING)
    pen = Pen.objects.create(code="C-01", name="Corral 1", capacity_head=120)
    feed = FeedType.objects.create(name="Maíz molido")
    ration = Ration.objects.create(name="Terminación 80/20")
    RationLine.objects.create(
        ration=ration, feed_type=feed, proportion="80", dry_matter_pct="88"
    )
    return client, pen, feed, ration


# --- catalogs ----------------------------------------------------------------

def test_ration_carries_its_composition_lines():
    _, _, feed, ration = _fixtures()
    assert ration.lines.count() == 1
    line = ration.lines.get()
    assert line.feed_type_id == feed.id
    assert line.proportion == Decimal("80.000")
    assert line.dry_matter_pct == Decimal("88.000")


# --- loading order (the plan) ------------------------------------------------

def test_loading_order_posts_no_ledger_entry():
    client, pen, _, ration = _fixtures()
    order = register_loading_order(
        pen=pen, ration=ration, date="2026-07-24", planned_as_fed_kg="2400"
    )
    assert isinstance(order, LoadingOrder)
    assert LedgerEntry.objects.filter(account=client.account).count() == 0
    client.account.refresh_from_db()
    assert client.account.balance_cached == Decimal("0")


def test_loading_order_on_inactive_pen_is_rejected():
    _, pen, _, ration = _fixtures()
    pen.status = Pen.Status.INACTIVE
    pen.save()
    with pytest.raises(ValidationError):
        register_loading_order(
            pen=pen, ration=ration, date="2026-07-24", planned_as_fed_kg="2400"
        )


def test_loading_order_with_inactive_ration_is_rejected():
    _, pen, _, ration = _fixtures()
    ration.is_active = False
    ration.save()
    with pytest.raises(ValidationError):
        register_loading_order(
            pen=pen, ration=ration, date="2026-07-24", planned_as_fed_kg="2400"
        )


# --- bunk score (the reading) ------------------------------------------------

def test_bunk_score_posts_no_ledger_entry():
    client, pen, _, _ = _fixtures()
    score = register_bunk_score(pen=pen, date="2026-07-24", score=2)
    assert isinstance(score, BunkScore)
    assert LedgerEntry.objects.filter(account=client.account).count() == 0


def test_bunk_score_out_of_range_is_rejected():
    _, pen, _, _ = _fixtures()
    with pytest.raises(ValidationError):
        register_bunk_score(pen=pen, date="2026-07-24", score=7)


def test_bunk_score_on_inactive_pen_is_rejected():
    _, pen, _, _ = _fixtures()
    pen.status = Pen.Status.INACTIVE
    pen.save()
    with pytest.raises(ValidationError):
        register_bunk_score(pen=pen, date="2026-07-24", score=2)


# --- executed ration groups by pen; cost summary reads it --------------------

def test_feeding_can_be_grouped_by_pen_and_still_charges():
    client, pen, feed, _ = _fixtures()
    lot = Lot.objects.create(
        client=client, code="L-1", head_count=100, total_weight=Decimal("45000")
    )
    feeding = register_feeding(
        client=client, feed_type=feed, quantity="1000", unit_price="285",
        origin=FeedingEvent.Origin.OWN_STOCK, date="2026-07-24", lot=lot, pen=pen,
    )
    assert feeding.pen_id == pen.id
    # The charge is unchanged by the pen grouping (adr-33 decision 3).
    assert LedgerEntry.objects.filter(account=client.account).count() == 1


def test_pen_cost_summary_totals_own_stock_feed_per_pen():
    client, pen, feed, _ = _fixtures()
    lot = Lot.objects.create(
        client=client, code="L-1", head_count=100, total_weight=Decimal("45000")
    )
    register_feeding(
        client=client, feed_type=feed, quantity="1000", unit_price="285",
        origin=FeedingEvent.Origin.OWN_STOCK, date="2026-07-24", lot=lot, pen=pen,
    )
    # Client-stock feed: kilos count, cost does not (billing follows origin).
    register_feeding(
        client=client, feed_type=feed, quantity="500", unit_price="285",
        origin=FeedingEvent.Origin.CLIENT_STOCK, date="2026-07-24", lot=lot, pen=pen,
    )
    summary = pen_cost_summary(client=client)
    assert len(summary) == 1
    row = summary[0]
    assert row["pen"] == pen.id
    assert row["code"] == "C-01"
    assert row["kilos_fed"] == Decimal("1500.00")
    assert row["feed_cost"] == Decimal("285000.0000")


def test_feeding_without_a_pen_stays_valid_and_is_not_summarised():
    client, _, feed, _ = _fixtures()
    lot = Lot.objects.create(
        client=client, code="L-2", head_count=50, total_weight=Decimal("22000")
    )
    register_feeding(
        client=client, feed_type=feed, quantity="800", unit_price="285",
        origin=FeedingEvent.Origin.OWN_STOCK, date="2026-07-24", lot=lot,
    )
    assert pen_cost_summary(client=client) == []
