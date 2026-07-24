"""The IPCVA parser, against a REAL page captured from the live site.

fixture_ipcva.html is the actual "Precios en Pie" (vista_precios.php?id=1) data
table for Novillos / ARGENTINA, Jan–Jun 2025, trimmed to the price table. The
values below are read off that real response — this locks the parser against
production HTML, not an imagined shape (docs/feedlot ADR-30 rule 3).
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from apps.market.connectors.base import ConnectorError
from apps.market.connectors.ipcva import IpcvaConnector

FIXTURES = Path(__file__).parent


def _prices():
    payload = (FIXTURES / "fixture_ipcva.html").read_bytes()
    return IpcvaConnector().parse(payload, target_date=date(2025, 6, 30))


def test_every_weight_band_becomes_its_own_category():
    cats = {p.category for p in _prices()}
    assert "Novillos 390-430" in cats
    assert "Novillos 520+" in cats
    assert "Novillos Novillo de Exportación" in cats


def test_first_week_values_are_read_off_the_real_table():
    prices = _prices()
    row = {p.category: p for p in prices if p.date == date(2025, 1, 7)}
    assert row["Novillos 390-430"].price_avg == Decimal("2.37")
    assert row["Novillos 520+"].price_avg == Decimal("2.09")
    assert row["Novillos Novillo de Exportación"].price_avg == Decimal("2.25")


def test_row_date_comes_from_the_row_not_the_target():
    # IPCVA is a range query: each row carries its own week's date, unlike Cañuelas.
    dates = {p.date for p in _prices()}
    assert date(2025, 1, 7) in dates
    assert date(2025, 1, 14) in dates
    assert all(d.year == 2025 for d in dates)


def test_currency_is_recorded_as_usd_not_ars():
    # The unit differs from Cañuelas on purpose; every row must say so (ADR-30 r8).
    assert all(p.raw.get("currency") == "USD" for p in _prices())


def test_spanish_month_abbreviations_are_parsed():
    dates = {p.date for p in _prices()}
    assert date(2025, 2, 4) in dates  # '04-feb-25'
    assert date(2025, 3, 4) in dates  # '04-mar-25'


def test_table_present_but_no_date_rows_yields_empty():
    empty = (
        b"<html><body><table>"
        b"<tr><td>Precios Internacionales</td></tr>"
        b"<tr><td>Fecha</td><td>Novillos</td></tr>"
        b"<tr><td>ARGENTINA</td></tr>"
        b"<tr><td>390-430</td><td>520+</td></tr>"
        b"</table></body></html>"
    )
    assert IpcvaConnector().parse(empty, target_date=date(2025, 6, 30)) == []


def test_no_price_table_raises_connector_error():
    with pytest.raises(ConnectorError):
        IpcvaConnector().parse(b"<html><body>sin tablas</body></html>", target_date=date(2025, 6, 30))


def test_raw_payload_is_kept_for_audit():
    assert "cells" in _prices()[0].raw


def test_default_target_date_has_no_lag():
    assert IpcvaConnector().default_target_date(date(2026, 7, 24)) == date(2026, 7, 24)


def test_build_form_encodes_the_range_and_selection():
    form = IpcvaConnector().build_form(date(2025, 3, 10), date(2025, 6, 30))
    assert form["mes_desde"] == "03-01"
    assert form["ano_desde"] == "2025"
    assert form["mes_hasta"] == "06-30"  # month-end of the target month
    assert form["ano_hasta"] == "2025"
    assert form["categorias[]"] == "1"
    assert form["paises[]"] == "1"


def test_fetch_window_reaches_months_back_from_the_target():
    from_date, to_date = IpcvaConnector()._window(date(2025, 6, 30))
    assert from_date == date(2025, 3, 1)  # 3 months back, first of month
    assert to_date == date(2025, 6, 30)


def test_fetch_window_crosses_the_year_boundary():
    from_date, _ = IpcvaConnector()._window(date(2025, 2, 15))
    assert from_date == date(2024, 11, 1)
