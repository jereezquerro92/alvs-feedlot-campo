"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""The Cañuelas parser, against a fixture that mirrors the real column layout.

The fixture is bytes encoded in cp1252 exactly like the live site, so the encoding
handling is exercised, not assumed.

NOTE FOR CLAUDE CODE: replace fixture_canuelas.html with a real populated page
captured from the live site (a closed, non-provisional day) to lock the parser
against production HTML. The structure here matches what was observed on
2026-07-23 but a real day's page is the ground truth.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from apps.market.connectors.canuelas import CanuelasConnector
from apps.market.connectors.base import ConnectorError

FIXTURES = Path(__file__).parent


def _read(name):
    return (FIXTURES / name).read_bytes()


def test_parses_every_category_row():
    prices = CanuelasConnector().parse(_read("fixture_canuelas.html"), target_date=date(2026, 7, 23))
    assert len(prices) == 3
    cats = {p.category for p in prices}
    assert "Novillos 431/460 Kg." in cats


def test_reads_all_price_columns_into_the_right_fields():
    prices = CanuelasConnector().parse(_read("fixture_canuelas.html"), target_date=date(2026, 7, 23))
    novillos = next(p for p in prices if p.category.startswith("Novillos"))
    assert novillos.price_min == Decimal("2100.00")
    assert novillos.price_max == Decimal("2850.50")
    assert novillos.price_avg == Decimal("2480.75")
    assert novillos.price_median == Decimal("2500.00")
    assert novillos.head_count == 320


def test_argentine_number_format_is_parsed():
    # '2.480,75' -> 2480.75, not 2.48075 and not 248075
    prices = CanuelasConnector().parse(_read("fixture_canuelas.html"), target_date=date(2026, 7, 23))
    assert next(p for p in prices if p.category.startswith("Vacas")).price_avg == Decimal("1520.25")


def test_target_date_is_stamped_on_every_row():
    d = date(2026, 7, 23)
    prices = CanuelasConnector().parse(_read("fixture_canuelas.html"), target_date=d)
    assert all(p.date == d for p in prices)


def test_provisional_page_yields_no_rows():
    prices = CanuelasConnector().parse(
        _read("fixture_canuelas_provisorio.html"), target_date=date(2026, 7, 24)
    )
    assert prices == []


def test_default_target_date_lags_one_day():
    assert CanuelasConnector().default_target_date(date(2026, 7, 24)) == date(2026, 7, 23)


def test_unrecognisable_html_raises_connector_error():
    with pytest.raises(ConnectorError):
        CanuelasConnector().parse(b"<html><body>nada de tablas</body></html>", target_date=date(2026, 7, 23))


def test_raw_payload_is_kept_for_audit():
    prices = CanuelasConnector().parse(_read("fixture_canuelas.html"), target_date=date(2026, 7, 23))
    assert "cells" in prices[0].raw


def test_build_form_posts_the_closed_day_in_dd_mm_yyyy():
    # `fetch` is network-excluded, so the POST body it sends is covered here instead.
    form = CanuelasConnector().build_form(date(2026, 7, 21))
    assert form["txtFechaIni"] == "21/07/2026"
    assert form["txtFechaFin"] == "21/07/2026"
    # The hidden fields the DLL expects must ride along unchanged.
    assert form["USUARIO"] == "SIN IDENTIFICAR"
    assert "OPCIONMENU" in form


def _table_html(rows: list[str]) -> bytes:
    header = (
        "<html><body><table>"
        "<tr><th>Categoría</th><th>Precios</th><th></th><th></th><th></th>"
        "<th>Totales</th><th></th><th></th><th>Prom.</th></tr>"
        "<tr><th></th><th>Mínimo</th><th>Máximo</th><th>Promedio</th><th>Mediana</th>"
        "<th>Cabezas</th><th>Importe</th><th>Kgs</th><th>Kgs</th></tr>"
    )
    return (header + "".join(rows) + "</table></body></html>").encode("cp1252")


def test_fractional_head_count_is_rejected_not_truncated():
    html = _table_html([
        "<tr><td>Novillos 431/460 Kg.</td><td>2.100,00</td><td>2.850,50</td>"
        "<td>2.480,75</td><td>2.500,00</td><td>320,5</td><td>1</td><td>1</td><td>1</td></tr>",
        "<tr><td>Vacas Buenas</td><td>1.200,00</td><td>1.800,00</td>"
        "<td>1.520,25</td><td>1.510,00</td><td>95</td><td>1</td><td>1</td><td>1</td></tr>",
    ])
    prices = CanuelasConnector().parse(html, target_date=date(2026, 7, 23))
    cats = {p.category for p in prices}
    assert "Novillos 431/460 Kg." not in cats
    assert "Vacas Buenas" in cats
    assert next(p for p in prices if p.category.startswith("Vacas")).head_count == 95


def test_non_positive_price_avg_is_rejected():
    html = _table_html([
        "<tr><td>Novillos 431/460 Kg.</td><td>0,00</td><td>0,00</td>"
        "<td>0,00</td><td>0,00</td><td>10</td><td>1</td><td>1</td><td>1</td></tr>",
        "<tr><td>Vacas Buenas</td><td>1.200,00</td><td>1.800,00</td>"
        "<td>1.520,25</td><td>1.510,00</td><td>95</td><td>1</td><td>1</td><td>1</td></tr>",
    ])
    prices = CanuelasConnector().parse(html, target_date=date(2026, 7, 23))
    assert len(prices) == 1
    assert prices[0].category.startswith("Vacas")
