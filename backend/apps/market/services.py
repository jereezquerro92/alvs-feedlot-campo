"""Market ingest — the only sanctioned way to persist prices.

Idempotent by (source, category, date): re-running an ingest updates the row's
numbers from the fresh payload instead of duplicating it. This mirrors the rest
of the system — the source is the truth, the row is a cache of the latest read.

`ingest_source` isolates one source: it fetches, parses and upserts, and lets a
ConnectorError bubble up so the *caller* (the command) can decide to keep going
with the other sources. No source failure is swallowed silently here.
"""

from dataclasses import dataclass
from datetime import date

from django.db import transaction

from apps.market.connectors import get_connector
from apps.market.connectors.base import ParsedPrice
from apps.market.models import MarketPrice, MarketSource


@dataclass
class IngestResult:
    source: str
    created: int
    updated: int
    rows: int

    @property
    def summary(self):
        return f"{self.source}: {self.rows} filas ({self.created} nuevas, {self.updated} actualizadas)"


@transaction.atomic
def upsert_price(*, source: MarketSource, parsed: ParsedPrice) -> bool:
    """Insert or update one price row. Returns True if created, False if updated."""
    _, created = MarketPrice.objects.update_or_create(
        source=source,
        category=parsed.category,
        date=parsed.date,
        defaults={
            "price_avg": parsed.price_avg,
            "price_min": parsed.price_min,
            "price_max": parsed.price_max,
            "price_median": parsed.price_median,
            "head_count": parsed.head_count,
            "raw": parsed.raw,
        },
    )
    return created


def persist(*, source: MarketSource, prices: list[ParsedPrice]) -> IngestResult:
    """Persist already-parsed prices for a source. Used by connectors and by tests."""
    created = updated = 0
    for parsed in prices:
        if upsert_price(source=source, parsed=parsed):
            created += 1
        else:
            updated += 1
    return IngestResult(source=source.slug, created=created, updated=updated, rows=len(prices))


def ingest_source(*, source: MarketSource, target_date: date = None) -> IngestResult:
    """Fetch, parse and persist one automated source. Raises ConnectorError on failure."""
    connector = get_connector(source.slug)
    if connector is None:
        # Manual source: nothing to fetch.
        return IngestResult(source=source.slug, created=0, updated=0, rows=0)

    if target_date is None and hasattr(connector, "default_target_date"):
        target_date = connector.default_target_date(date.today())
    target_date = target_date or date.today()

    prices = connector.collect(target_date=target_date)
    return persist(source=source, prices=prices)


def register_manual_price(
    *, source: MarketSource, category, date, price_avg,
    price_min=None, price_max=None, price_median=None, head_count=None,
) -> MarketPrice:
    """Load a price by hand. The always-available fallback (docs/feedlot/06b)."""
    parsed = ParsedPrice(
        category=category, date=date, price_avg=price_avg, price_min=price_min,
        price_max=price_max, price_median=price_median, head_count=head_count,
        raw={"manual": True},
    )
    upsert_price(source=source, parsed=parsed)
    return MarketPrice.objects.get(source=source, category=category, date=date)


def latest_price(*, source_slug, category, on_or_before=None):
    """Most recent price for a category from a source, at or before a date.

    Tolerance to source outages: if today's ingest failed, callers still get the
    last known value instead of nothing (docs/feedlot/06b).
    """
    qs = MarketPrice.objects.filter(source__slug=source_slug, category=category)
    if on_or_before is not None:
        qs = qs.filter(date__lte=on_or_before)
    return qs.order_by("-date").first()
