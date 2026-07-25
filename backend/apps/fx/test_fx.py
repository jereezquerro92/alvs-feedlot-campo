"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Phase 12 (fx + gross margin): reference exchange rates and derived margin (adr-39).

FxRate is idempotent by (currency, date, source) and never redenominates the ledger.
`gross_margin` crosses kilos produced × market price against period cost, in ARS and
optionally in another currency — `null`+reason when any input is missing, never a filled 0.
"""

from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.clients.models import Client
from apps.fx.models import FxRate
from apps.fx.services import convert_ars, latest_rate, register_fx_rate
from apps.feed.services import register_feeding
from apps.feed.models import FeedType
from apps.ledger.models import LedgerEntry
from apps.livestock.models import Animal
from apps.livestock.services import register_weighing
from apps.market.models import MarketPrice, MarketSource
from apps.metrics import services

pytestmark = pytest.mark.django_db


# --- fx rate -----------------------------------------------------------------

def test_register_fx_rate_is_idempotent_by_triple():
    register_fx_rate(currency="USD", date=date(2026, 7, 20), rate=Decimal("1000"))
    register_fx_rate(currency="USD", date=date(2026, 7, 20), rate=Decimal("1050"))
    rows = FxRate.objects.filter(currency="USD", date=date(2026, 7, 20), source="manual")
    assert rows.count() == 1
    assert rows.first().rate == Decimal("1050.000000")


def test_register_fx_rate_rejects_non_positive():
    with pytest.raises(ValidationError):
        register_fx_rate(currency="USD", date=date(2026, 7, 20), rate=Decimal("0"))
    assert FxRate.objects.count() == 0


def test_latest_rate_returns_last_known_on_or_before():
    register_fx_rate(currency="USD", date=date(2026, 7, 1), rate=Decimal("900"))
    register_fx_rate(currency="USD", date=date(2026, 7, 15), rate=Decimal("1000"))
    assert latest_rate(currency="USD").rate == Decimal("1000.000000")
    assert latest_rate(currency="USD", on_or_before=date(2026, 7, 10)).rate == Decimal("900.000000")
    assert latest_rate(currency="EUR") is None


def test_convert_ars_divides_by_the_rate():
    register_fx_rate(currency="USD", date=date(2026, 7, 15), rate=Decimal("1000"))
    converted, row = convert_ars(amount_ars=Decimal("50000"), currency="USD")
    assert converted == Decimal("50")
    assert row.rate == Decimal("1000.000000")
    none, no_row = convert_ars(amount_ars=Decimal("50000"), currency="EUR")
    assert none is None and no_row is None


def test_fx_rate_posts_no_ledger_entry():
    register_fx_rate(currency="USD", date=date(2026, 7, 15), rate=Decimal("1000"))
    assert LedgerEntry.objects.count() == 0


# --- gross margin ------------------------------------------------------------

def _client():
    return Client.objects.create(name="La Esperanza", kind=Client.Kind.BOARDING)


def _animal(client):
    return Animal.objects.create(
        client=client, ear_tag="A-001", category="steer", entry_date="2026-01-10",
        entry_weight=Decimal("320"), current_weight=Decimal("320"),
    )


def _grow(client):
    animal = _animal(client)
    register_weighing(animal=animal, weight="320", date="2026-02-01")
    register_weighing(animal=animal, weight="380", date="2026-03-03")  # +60 kg
    return animal


def _price(avg="2000", on=date(2026, 3, 1)):
    source, _ = MarketSource.objects.get_or_create(slug="canuelas", defaults={"name": "Cañuelas"})
    MarketPrice.objects.update_or_create(
        source=source, category="steer", date=on, defaults={"price_avg": Decimal(avg)}
    )
    return source


def _feed_cost(client, animal):
    feed = FeedType.objects.create(name="Maíz")
    register_feeding(
        client=client, animal=animal, feed_type=feed, quantity=Decimal("300"),
        unit_price=Decimal("100"), date="2026-02-15", origin="own_stock",
    )  # 300 × 100 = 30000 ARS debit


def test_gross_margin_is_income_minus_cost():
    client = _client()
    animal = _grow(client)
    _price(avg="2000")  # 60 kg × 2000 = 120000 income
    _feed_cost(client, animal)  # 30000 cost
    result = services.gross_margin(
        client=client, end=date(2026, 3, 31), price_source="canuelas", category="steer"
    )
    assert result["kilos_gained"] == Decimal("60")
    assert result["income"] == Decimal("120000")
    assert result["cost"] == Decimal("30000")
    assert result["margin"] == Decimal("90000")
    assert result["not_calculable"] == ""


def test_gross_margin_null_when_no_measured_growth():
    client = _client()
    _animal(client)  # no weighings → no measured segment
    _price()
    result = services.gross_margin(
        client=client, end=date(2026, 3, 31), price_source="canuelas", category="steer"
    )
    assert result["margin"] is None
    assert result["not_calculable"] == "no_measured_growth"


def test_gross_margin_null_when_no_reference_price():
    client = _client()
    _grow(client)  # growth exists, but no MarketPrice loaded
    result = services.gross_margin(
        client=client, end=date(2026, 3, 31), price_source="canuelas", category="steer"
    )
    assert result["margin"] is None
    assert result["not_calculable"] == "no_reference_price"


def test_gross_margin_expressed_in_usd_via_fx():
    client = _client()
    animal = _grow(client)
    _price(avg="2000")
    _feed_cost(client, animal)  # margin 90000 ARS
    register_fx_rate(currency="USD", date=date(2026, 3, 1), rate=Decimal("1000"))
    result = services.gross_margin(
        client=client, end=date(2026, 3, 31), price_source="canuelas",
        category="steer", currency="USD",
    )
    assert result["margin"] == Decimal("90000")
    assert result["currency"] == "USD"
    assert result["margin_currency"] == Decimal("90")  # 90000 / 1000
    assert result["not_calculable"] == ""


def test_gross_margin_usd_null_when_no_fx_rate():
    client = _client()
    animal = _grow(client)
    _price(avg="2000")
    _feed_cost(client, animal)
    result = services.gross_margin(
        client=client, end=date(2026, 3, 31), price_source="canuelas",
        category="steer", currency="USD",  # no FxRate loaded
    )
    assert result["margin"] == Decimal("90000")  # ARS margin still returned
    assert result["margin_currency"] is None
    assert result["not_calculable"] == "no_fx_rate"
