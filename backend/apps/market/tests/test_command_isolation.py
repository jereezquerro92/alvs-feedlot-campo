"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""The ingest command keeps going when one source fails (docs/feedlot/06b)."""

from datetime import date
from decimal import Decimal
from io import StringIO
from unittest import mock

import pytest
from django.core.management import call_command

from apps.market.connectors.base import ConnectorError, ParsedPrice
from apps.market.models import MarketPrice, MarketSource

pytestmark = pytest.mark.django_db


def test_a_failing_source_does_not_stop_the_others():
    MarketSource.objects.get_or_create(slug="canuelas", defaults={"name": "Cañuelas", "is_automated": True})
    MarketSource.objects.get_or_create(slug="ipcva", defaults={"name": "IPCVA", "is_automated": True})

    def fake_ingest(*, source, target_date=None):
        from apps.market.services import IngestResult
        if source.slug == "ipcva":
            raise ConnectorError("endpoint no cableado")
        MarketPrice.objects.create(
            source=source, category="Novillos", date=date(2026, 7, 23), price_avg=Decimal("2480.75")
        )
        return IngestResult(source="canuelas", created=1, updated=0, rows=1)

    out, err = StringIO(), StringIO()
    with mock.patch("apps.market.management.commands.ingest_prices.ingest_source", fake_ingest):
        call_command("ingest_prices", stdout=out, stderr=err)

    # Cañuelas persisted despite IPCVA failing.
    assert MarketPrice.objects.filter(source__slug="canuelas").count() == 1
    assert "FALLÓ" in err.getvalue()


def test_collect_wraps_oserror_as_connector_error():
    """Network failures at fetch become ConnectorError (adr-30 rule 7)."""
    from apps.market.connectors.base import BaseConnector

    class Boom(BaseConnector):
        slug = "boom"

        def fetch(self, *, target_date):
            raise TimeoutError("timed out")

        def parse(self, payload, *, target_date):
            return []

    with pytest.raises(ConnectorError, match="timed out"):
        Boom().collect(target_date=date(2026, 7, 23))


def test_ingest_prices_isolates_oserror_via_connector_boundary():
    """URLError/timeout from fetch must not abort the whole ingest run."""
    MarketSource.objects.get_or_create(slug="canuelas", defaults={"name": "Cañuelas", "is_automated": True})
    MarketSource.objects.get_or_create(slug="ipcva", defaults={"name": "IPCVA", "is_automated": True})

    def fake_ingest(*, source, target_date=None):
        from apps.market.services import IngestResult
        from apps.market.connectors.base import BaseConnector

        class Flaky(BaseConnector):
            def fetch(self, *, target_date):
                raise OSError("connection reset")

            def parse(self, payload, *, target_date):
                return []

        if source.slug == "ipcva":
            # Simulate ingest_source → connector.collect wrapping OSError.
            Flaky().collect(target_date=target_date or date(2026, 7, 23))
        MarketPrice.objects.create(
            source=source, category="Novillos", date=date(2026, 7, 23), price_avg=Decimal("2480.75")
        )
        return IngestResult(source="canuelas", created=1, updated=0, rows=1)

    out, err = StringIO(), StringIO()
    with mock.patch("apps.market.management.commands.ingest_prices.ingest_source", fake_ingest):
        call_command("ingest_prices", stdout=out, stderr=err)

    assert MarketPrice.objects.filter(source__slug="canuelas").count() == 1
    assert "FALLÓ" in err.getvalue()


def test_routes_resolve():
    from django.urls import reverse
    assert reverse("market-source-list") == "/api/market-sources/"
    assert reverse("market-price-list") == "/api/market-prices/"
