"""Connector framework: one class per automated source.

A connector turns raw source bytes into a list of ParsedPrice rows. It does NOT
touch the database and it does NOT do network on its own during tests — `fetch`
is separate from `parse` precisely so `parse` can be tested against a fixture
without hitting the live site. The service layer (services.ingest_source) is what
persists, idempotently.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class ParsedPrice:
    """One category's numbers for one date, as read from a source. Source-agnostic."""

    category: str
    date: date
    price_avg: Optional[Decimal] = None
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None
    price_median: Optional[Decimal] = None
    head_count: Optional[int] = None
    raw: dict = field(default_factory=dict)


class ConnectorError(Exception):
    """Raised when a source can't be reached or its shape changed. Caught per-source
    by the ingest command so one broken source never stops the others."""


class BaseConnector:
    slug: str = ""

    def fetch(self, *, target_date: date) -> bytes:
        """Return the raw response bytes for the given date. Network lives here."""
        raise NotImplementedError

    def parse(self, payload: bytes, *, target_date: date) -> list[ParsedPrice]:
        """Turn raw bytes into ParsedPrice rows. Pure: no network, no DB."""
        raise NotImplementedError

    def collect(self, *, target_date: date) -> list[ParsedPrice]:
        """fetch + parse. Overridable if a source needs a different shape."""
        return self.parse(self.fetch(target_date=target_date), target_date=target_date)
