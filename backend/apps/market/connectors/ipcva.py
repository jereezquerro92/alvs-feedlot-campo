"""IPCVA — second automated source (docs/feedlot/06c).

Chosen over ROSGAN because its stat pages are server-rendered rather than built
in the browser. Verified against the live site: the "Precios en Pie" view
(`vista_precios.php?id=1`) is driven by an HTML form (`name="datos"`) posted back
to the same URL with a date range (`mes_desde`/`ano_desde`/`mes_hasta`/`ano_hasta`),
a category set (`categorias[]`) and a country set (`paises[]`). The response is a
server-rendered page and the numbers live in a plain HTML **table** — not in a
JavaScript chart — so `parse` reads them directly, no browser needed.

Unit caveat, on purpose and recorded here: this series is the **international
Novillos index in USD/kg** (the page titles itself "Precios Internacionales"),
NOT ARS like Cañuelas. That is fine and deliberate — the two sources measure
different things at different cadences and are kept apart by `source`, never
averaged (docs/feedlot ADR-30 rule 8). Every row this connector emits records
`currency: "USD"` in `raw` so no consumer mistakes it for the ARS ledger unit.

The table carries weekly Novillos prices split by carcass-weight band
(390-430, …, 520+, plus "Novillo de Exportación"). Each band is published as its
own number, so each band becomes its own `category` ("Novillos <band>") and its
own `ParsedPrice` — nothing is aggregated, so nothing is fabricated. The header
row is read to map columns, so a re-order upstream never shifts a value into the
wrong band.

Three states, three answers (ADR-30 rule 5):
  - a table with date rows            → parse them;
  - a table present but with no rows  → return [] (a window with no data yet);
  - no price table at all             → ConnectorError (the HTML changed).
"""

import calendar
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from apps.market.connectors.base import BaseConnector, ConnectorError, ParsedPrice

STATS_URL = "https://ipcva.agrositio.com/estadisticas/vista_precios.php?id=1"

# How far back the fetch window reaches from the target month, in months. The
# series is weekly; a few months keeps the ingest idempotent and catches
# late-published weeks without pulling the whole history every run.
_LOOKBACK_MONTHS = 3

# Novillos / ARGENTINA — the feedlot's headline category, one country. Keeping a
# single category per fetch keeps the table's header unambiguous.
_CATEGORY_CODE = "1"
_COUNTRY_CODE = "1"
_CATEGORY_LABEL = "Novillos"

_USER_AGENT = "Mozilla/5.0 (compatible; alvs-feedlot/1.0)"

# Spanish three-letter month abbreviations as the site prints them ('07-ene-25').
_MONTHS = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}
_DATE_RE = re.compile(r"^\s*(\d{2})-([a-z]{3})-(\d{2})\s*$", re.IGNORECASE)


def _to_decimal(cell: str):
    """Parse an AR-formatted number ('1.234,56' / '2,37') to Decimal, or None."""
    cell = (cell or "").strip()
    if not cell or cell in {"-", "s/c", "S/C"}:
        return None
    cell = cell.replace(".", "").replace(",", ".")
    try:
        return Decimal(cell)
    except InvalidOperation:
        return None


def _parse_row_date(cell: str):
    """'07-ene-25' → date(2025, 1, 7), or None if the cell is not a date."""
    m = _DATE_RE.match(cell or "")
    if not m:
        return None
    day, mon, yy = m.group(1), m.group(2).lower(), m.group(3)
    month = _MONTHS.get(mon)
    if month is None:
        return None
    try:
        return date(2000 + int(yy), month, int(day))
    except ValueError:
        return None


class IpcvaConnector(BaseConnector):
    slug = "ipcva"

    def default_target_date(self, today: date) -> date:
        """No fixed lag: the fetch window reaches back months, so today is fine."""
        return today

    def build_form(self, from_date: date, to_date: date) -> dict:
        """The POST body for a date-range query. Pure — testable without network."""
        last_day = calendar.monthrange(to_date.year, to_date.month)[1]
        return {
            "mes_desde": f"{from_date.month:02d}-01",
            "ano_desde": str(from_date.year),
            "mes_hasta": f"{to_date.month:02d}-{last_day:02d}",
            "ano_hasta": str(to_date.year),
            "categorias[]": _CATEGORY_CODE,
            "paises[]": _COUNTRY_CODE,
            "tipo_grafico": "line",
        }

    def _window(self, target_date: date):
        """(from_date, to_date) spanning _LOOKBACK_MONTHS back from the target month."""
        month = target_date.month - _LOOKBACK_MONTHS
        year = target_date.year
        while month <= 0:
            month += 12
            year -= 1
        return date(year, month, 1), target_date

    def fetch(self, *, target_date: date) -> bytes:  # pragma: no cover - network
        import urllib.parse
        import urllib.request

        from_date, to_date = self._window(target_date)
        data = urllib.parse.urlencode(self.build_form(from_date, to_date), doseq=True).encode("ascii")
        req = urllib.request.Request(
            STATS_URL,
            data=data,
            headers={
                "User-Agent": _USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()

    def parse(self, payload: bytes, *, target_date: date) -> list[ParsedPrice]:
        html = payload.decode("utf-8", errors="replace")
        tables = self._extract_tables(html)

        data_table = self._find_price_table(tables)
        if data_table is None:
            raise ConnectorError("IPCVA: no encuentro la tabla de precios (¿cambió el HTML?).")

        # First row whose first cell is a date splits header from body.
        first_data_idx = next(
            (i for i, row in enumerate(data_table) if row and _parse_row_date(row[0])),
            None,
        )
        if first_data_idx is None:
            # Table present (it carries the 'Fecha'/category header) but no date rows:
            # a window with no published data. Not an error (ADR-30 rule 5).
            return []

        body = data_table[first_data_idx:]
        n_price_cols = len(body[0]) - 1
        bands = self._band_labels(data_table[:first_data_idx], n_price_cols)
        country = self._country_label(data_table[:first_data_idx])

        parsed = []
        for row in body:
            row_date = _parse_row_date(row[0])
            if row_date is None:
                continue
            for col in range(1, len(row)):
                avg = _to_decimal(row[col])
                if avg is None:
                    continue
                band = bands[col - 1] if col - 1 < len(bands) else f"col{col}"
                category = f"{_CATEGORY_LABEL} {band}"[:60]
                parsed.append(
                    ParsedPrice(
                        category=category,
                        date=row_date,
                        price_avg=avg,
                        raw={
                            "currency": "USD",
                            "country": country,
                            "band": band,
                            "cells": row,
                        },
                    )
                )
        return parsed

    @staticmethod
    def _band_labels(header_rows, n_price_cols) -> list[str]:
        """The weight-band labels: the header row of exactly n_price_cols non-date cells."""
        for row in reversed(header_rows):
            if len(row) == n_price_cols and not any(_parse_row_date(c) for c in row):
                return [c.strip() for c in row]
        # No labelled header found: name bands by position so values still land.
        return [f"col{i + 1}" for i in range(n_price_cols)]

    @staticmethod
    def _country_label(header_rows) -> str:
        """A single-cell header row that is not the title is the country name."""
        for row in header_rows:
            if len(row) == 1 and "precios" not in row[0].lower():
                return row[0].strip()
        return ""

    @staticmethod
    def _extract_tables(html: str) -> list[list[list[str]]]:
        """Every <table> as a list of rows of cell-text."""
        from html.parser import HTMLParser

        class _Reader(HTMLParser):
            def __init__(self):
                super().__init__()
                self.tables, self._rows, self._cells, self._buf = [], None, None, ""
                self._in_cell = False

            def handle_starttag(self, tag, attrs):
                if tag == "table":
                    self._rows = []
                elif tag == "tr" and self._rows is not None:
                    self._cells = []
                elif tag in ("td", "th") and self._cells is not None:
                    self._in_cell, self._buf = True, ""

            def handle_endtag(self, tag):
                if tag in ("td", "th") and self._in_cell:
                    self._cells.append(self._buf.strip())
                    self._in_cell = False
                elif tag == "tr" and self._cells is not None:
                    if self._cells:
                        self._rows.append(self._cells)
                    self._cells = None
                elif tag == "table" and self._rows is not None:
                    self.tables.append(self._rows)
                    self._rows = None

            def handle_data(self, data):
                if self._in_cell:
                    self._buf += data

        reader = _Reader()
        reader.feed(html)
        return reader.tables

    @staticmethod
    def _find_price_table(tables) -> list[list[str]]:
        """The price table: it carries a 'Fecha' + category header (data rows optional)."""
        for table in tables:
            flat = " ".join(" ".join(r) for r in table[:5]).lower()
            if "fecha" in flat and _CATEGORY_LABEL.lower() in flat:
                return table
        return None
