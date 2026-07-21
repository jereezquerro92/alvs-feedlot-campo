"""Phase 3: the dashboard numbers. A wrong metric is worse than a missing one."""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.clients.models import Client
from apps.feed.models import FeedingEvent, FeedType
from apps.feed.services import register_feeding
from apps.livestock.models import Animal
from apps.livestock.services import (
    create_lot_intake,
    register_death,
    register_weighing,
)
from apps.ledger.services import register_payment
from apps.metrics import services
from apps.sanitary.models import HealthProduct
from apps.sanitary.services import register_health_event

pytestmark = pytest.mark.django_db


def _client(name="La Esperanza"):
    return Client.objects.create(name=name, kind=Client.Kind.BOARDING)


def _animal(client, ear_tag="A-001", weight="320"):
    return Animal.objects.create(
        client=client, ear_tag=ear_tag, category="steer", entry_date="2026-01-10",
        entry_weight=Decimal(weight), current_weight=Decimal(weight),
    )


# --- herd --------------------------------------------------------------------

def test_herd_snapshot_counts_animals_and_lots():
    client = _client()
    _animal(client, "A-001", "300")
    _animal(client, "A-002", "340")
    create_lot_intake(client=client, date="2026-01-10", code="L-01", head_count=10, total_weight="3200")
    snap = services.herd_snapshot(client=client)
    assert snap["head_count"] == 12
    assert snap["total_weight"] == Decimal("3840.00")
    assert snap["average_weight"] == Decimal("320")


def test_dead_animals_leave_the_herd():
    client = _client()
    animal = _animal(client)
    register_death(animal=animal, date="2026-02-01")
    assert services.herd_snapshot(client=client)["head_count"] == 0


# --- growth ------------------------------------------------------------------

def test_kilos_gained_sums_measured_segments():
    client = _client()
    animal = _animal(client)
    register_weighing(animal=animal, weight="320", date="2026-02-01")
    register_weighing(animal=animal, weight="380", date="2026-03-03")
    result = services.kilos_gained(client=client)
    assert result["kilos_gained"] == Decimal("60")
    assert result["segments_measured"] == 1
    assert result["segments_skipped"] == 0


def test_lot_gain_multiplies_per_head_delta_by_head_count():
    client = _client()
    _, lot = create_lot_intake(
        client=client, date="2026-01-10", code="L-01", head_count=50, total_weight="16000"
    )
    register_weighing(lot=lot, weight="16000", date="2026-02-01", head_count=50)  # 320/head
    register_weighing(lot=lot, weight="17500", date="2026-03-03", head_count=50)  # 350/head
    # +30 kg per head across 50 head = 1500 kg, which happens to equal the total delta here.
    assert services.kilos_gained(client=client)["kilos_gained"] == Decimal("1500")


def test_segments_with_changed_head_count_are_skipped_not_guessed():
    client = _client()
    _, lot = create_lot_intake(
        client=client, date="2026-01-10", code="L-01", head_count=50, total_weight="16000"
    )
    register_weighing(lot=lot, weight="16000", date="2026-02-01", head_count=50)
    register_weighing(lot=lot, weight="20000", date="2026-03-03", head_count=62)
    result = services.kilos_gained(client=client)
    assert result["kilos_gained"] == Decimal("0")
    assert result["segments_measured"] == 0
    assert result["segments_skipped"] == 1


# --- conversion --------------------------------------------------------------

def test_conversion_is_feed_over_gain():
    client = _client()
    animal = _animal(client)
    register_weighing(animal=animal, weight="320", date="2026-02-01")
    register_weighing(animal=animal, weight="380", date="2026-03-03")
    register_feeding(
        client=client, feed_type=FeedType.objects.create(name="Maíz"), quantity="420",
        unit_price="285", origin=FeedingEvent.Origin.OWN_STOCK, date="2026-02-15", animal=animal,
    )
    result = services.conversion(client=client)
    assert result["conversion"] == Decimal("7")  # 420 kg fed / 60 kg gained
    assert result["not_calculable"] == ""


def test_conversion_is_none_when_no_growth_was_measured():
    client = _client()
    animal = _animal(client)
    register_feeding(
        client=client, feed_type=FeedType.objects.create(name="Maíz"), quantity="420",
        unit_price="285", origin=FeedingEvent.Origin.OWN_STOCK, date="2026-02-15", animal=animal,
    )
    result = services.conversion(client=client)
    assert result["conversion"] is None
    assert result["not_calculable"] == "no_measured_growth"


def test_conversion_is_none_when_the_animal_lost_weight():
    client = _client()
    animal = _animal(client)
    register_weighing(animal=animal, weight="380", date="2026-02-01")
    register_weighing(animal=animal, weight="360", date="2026-03-03")
    result = services.conversion(client=client)
    assert result["conversion"] is None
    assert result["not_calculable"] == "no_weight_gain"


# --- mortality ---------------------------------------------------------------

def test_mortality_rate_over_head_entered():
    client = _client()
    _, lot = create_lot_intake(
        client=client, date="2026-01-10", code="L-01", head_count=100, total_weight="32000"
    )
    register_death(lot=lot, date="2026-02-01", head_count=3, weight="960")
    result = services.mortality(client=client)
    assert result["dead_head"] == 3
    assert result["entered_head"] == 100
    assert result["rate"] == Decimal("0.03")


def test_mortality_rate_is_none_without_intake_in_the_period():
    client = _client()
    result = services.mortality(client=client, start="2026-01-01", end="2026-12-31")
    assert result["rate"] is None
    assert result["not_calculable"] == "no_intake_in_period"


def test_mortality_ignores_other_clients():
    client, other = _client(), _client("El Ombú")
    create_lot_intake(client=client, date="2026-01-10", code="L-01", head_count=10, total_weight="3200")
    _, foreign_lot = create_lot_intake(
        client=other, date="2026-01-10", code="L-02", head_count=10, total_weight="3200"
    )
    register_death(lot=foreign_lot, date="2026-02-01", head_count=2)
    assert services.mortality(client=client)["dead_head"] == 0


# --- cost and account --------------------------------------------------------

def test_cost_breakdown_separates_feeding_from_health():
    client = _client()
    animal = _animal(client)
    register_feeding(
        client=client, feed_type=FeedType.objects.create(name="Maíz"), quantity="100",
        unit_price="285", origin=FeedingEvent.Origin.OWN_STOCK, date="2026-02-15", animal=animal,
    )
    register_health_event(
        client=client, animal=animal, quantity="2", date="2026-02-16",
        product=HealthProduct.objects.create(name="Aftosa", unit_price=Decimal("1500")),
    )
    cost = services.cost_breakdown(client=client)
    assert cost["by_concept"]["feeding"] == Decimal("28500.00")
    assert cost["by_concept"]["health"] == Decimal("3000.00")
    assert cost["total"] == Decimal("31500.00")


def test_payments_are_not_counted_as_cost():
    client = _client()
    animal = _animal(client)
    register_feeding(
        client=client, feed_type=FeedType.objects.create(name="Maíz"), quantity="100",
        unit_price="285", origin=FeedingEvent.Origin.OWN_STOCK, date="2026-02-15", animal=animal,
    )
    register_payment(account=client.account, amount="10000", date="2026-02-20")
    assert services.cost_breakdown(client=client)["total"] == Decimal("28500.00")


def test_account_evolution_tracks_a_running_balance():
    client = _client()
    animal = _animal(client)
    register_feeding(
        client=client, feed_type=FeedType.objects.create(name="Maíz"), quantity="100",
        unit_price="285", origin=FeedingEvent.Origin.OWN_STOCK, date="2026-02-15", animal=animal,
    )
    register_payment(account=client.account, amount="8500", date="2026-02-20")
    evolution = services.account_evolution(client=client)
    assert evolution["opening_balance"] == Decimal("0")
    assert [p["balance"] for p in evolution["points"]] == [Decimal("28500.00"), Decimal("20000.00")]
    assert evolution["closing_balance"] == Decimal("20000.00")


def test_account_evolution_carries_an_opening_balance():
    client = _client()
    animal = _animal(client)
    register_feeding(
        client=client, feed_type=FeedType.objects.create(name="Maíz"), quantity="100",
        unit_price="285", origin=FeedingEvent.Origin.OWN_STOCK, date="2026-01-05", animal=animal,
    )
    evolution = services.account_evolution(client=client, start="2026-02-01")
    assert evolution["opening_balance"] == Decimal("28500.00")
    assert evolution["points"] == []


def test_daily_cost_groups_by_day():
    client = _client()
    animal = _animal(client)
    feed = FeedType.objects.create(name="Maíz")
    for day in ("2026-02-15", "2026-02-15", "2026-02-16"):
        register_feeding(
            client=client, feed_type=feed, quantity="100", unit_price="285",
            origin=FeedingEvent.Origin.OWN_STOCK, date=day, animal=animal,
        )
    rows = services.daily_cost(client=client)
    assert len(rows) == 2
    assert rows[0]["total"] == Decimal("57000.00")


# --- consistency -------------------------------------------------------------

def test_feeding_after_death_is_surfaced_as_an_inconsistency():
    client = _client()
    animal = _animal(client)
    register_death(animal=animal, date="2026-02-01")
    FeedingEvent.objects.create(
        client=client, animal=animal, feed_type=FeedType.objects.create(name="Maíz"),
        quantity=Decimal("10"), unit_price=Decimal("285"),
        origin=FeedingEvent.Origin.OWN_STOCK, date="2026-02-10",
    )
    findings = services.inconsistencies(client=client)
    assert len(findings) == 1
    assert findings[0]["kind"] == "feeding_after_death"


def test_clean_data_reports_no_inconsistencies():
    client = _client()
    _animal(client)
    assert services.inconsistencies(client=client) == []


# --- endpoints ---------------------------------------------------------------

@pytest.mark.parametrize(
    "name,path",
    [
        ("metrics-summary", "/api/clients/1/metrics/summary/"),
        ("metrics-daily-cost", "/api/clients/1/metrics/daily-cost/"),
        ("metrics-growth", "/api/clients/1/metrics/growth/"),
        ("metrics-conversion", "/api/clients/1/metrics/conversion/"),
        ("metrics-mortality", "/api/clients/1/metrics/mortality/"),
        ("metrics-account", "/api/clients/1/metrics/account/"),
    ],
)
def test_metric_routes_resolve(name, path):
    assert reverse(name, args=[1]) == path


def test_summary_endpoint_returns_every_block():
    client = _client()
    _animal(client)
    result = services.summary(client=client)
    assert set(result) == {
        "client", "period", "herd", "balance", "cost",
        "conversion", "mortality", "inconsistencies",
    }
