"""Ingest idempotency, manual load, and per-source failure isolation."""

from datetime import date
from decimal import Decimal

import pytest

from apps.market.connectors.base import ConnectorError, ParsedPrice
from apps.market.models import MarketPrice, MarketSource
from apps.market.services import (
    ingest_source,
    latest_price,
    persist,
    register_manual_price,
)

pytestmark = pytest.mark.django_db


def _source(slug="canuelas", automated=True):
    # The seed migration already created canuelas/ipcva/rosgan/manual, so reuse.
    source, _ = MarketSource.objects.get_or_create(
        slug=slug, defaults={"name": slug.title(), "is_automated": automated}
    )
    return source


def _price(category="Novillos", d="2026-07-23", avg="2480.75"):
    return ParsedPrice(category=category, date=date.fromisoformat(d), price_avg=Decimal(avg))


def test_persist_creates_rows():
    source = _source()
    result = persist(source=source, prices=[_price(), _price("Vacas", avg="1520.25")])
    assert result.created == 2
    assert MarketPrice.objects.count() == 2


def test_reingest_updates_not_duplicates():
    source = _source()
    persist(source=source, prices=[_price(avg="2480.75")])
    result = persist(source=source, prices=[_price(avg="2500.00")])  # same source/cat/date
    assert result.updated == 1
    assert MarketPrice.objects.count() == 1
    assert MarketPrice.objects.get().price_avg == Decimal("2500.00")


def test_same_category_different_date_is_a_new_row():
    source = _source()
    persist(source=source, prices=[_price(d="2026-07-23")])
    persist(source=source, prices=[_price(d="2026-07-24")])
    assert MarketPrice.objects.count() == 2


def test_manual_load_persists_a_price():
    source = _source("manual", automated=False)
    price = register_manual_price(
        source=source, category="Novillos", date=date(2026, 7, 23), price_avg=Decimal("2500"),
    )
    assert price.price_avg == Decimal("2500")
    assert price.raw == {"manual": True}


def test_manual_source_ingest_is_a_noop():
    source = _source("manual", automated=False)
    result = ingest_source(source=source)
    assert result.rows == 0


def test_latest_price_returns_most_recent():
    source = _source()
    persist(source=source, prices=[_price(d="2026-07-20", avg="2400")])
    persist(source=source, prices=[_price(d="2026-07-23", avg="2480.75")])
    latest = latest_price(source_slug="canuelas", category="Novillos")
    assert latest.date == date(2026, 7, 23)


def test_latest_price_respects_on_or_before():
    source = _source()
    persist(source=source, prices=[_price(d="2026-07-20", avg="2400")])
    persist(source=source, prices=[_price(d="2026-07-23", avg="2480.75")])
    older = latest_price(source_slug="canuelas", category="Novillos", on_or_before=date(2026, 7, 21))
    assert older.date == date(2026, 7, 20)


def test_ipcva_source_raises_until_wired():
    source = _source("ipcva")
    with pytest.raises(ConnectorError):
        ingest_source(source=source, target_date=date(2026, 7, 23))
