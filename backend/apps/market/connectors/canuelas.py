"""Mercado Agroganadero (Cañuelas) — primary daily source (docs/feedlot/06b).

Three things this site does that will bite a naive scraper, all handled here:

1. **Encoding is Windows-1252**, not UTF-8. Decoded explicitly as cp1252.
2. **Same-day data is provisional**: the page shows "PRECIOS PROVISORIOS" with an
   empty table until the day closes. We refuse to parse a provisional page and we
   run with a one-day lag by default.
3. **The date form drives the report.** The exact POST/GET contract must be
   confirmed against the live site (do this in Claude Code, network tab); the URL
   and params below are the integration point, isolated in `fetch`.

The parser reads the header row to map columns, so a column re-order upstream does
not silently shift values into the wrong field.
"""

import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from apps.market.connectors.base import BaseConnector, ConnectorError, ParsedPrice

# Categoría | Mínimo | Máximo | Promedio | Mediana | Cabezas | Importe | Kgs | Kgs prom
_COLUMN_ALIASES = {
    "categoria": "category",
    "minimo": "price_min",
    "maximo": "price_max",
    "promedio": "price_avg",
    "mediana": "price_median",
    "cabezas": "head_count",
}

_PROVISIONAL = "PROVISORIO"

# Integration point — confirm against the live site in Claude Code.
BASE_URL = "https://www.mercadoagroganadero.com.ar/dll/hacienda1.dll/haciinfo000502"


def _norm(text: str) -> str:
    """Lowercase, strip accents/spaces, for header matching."""
    text = text.strip().lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")):
        text = text.replace(a, b)
    return re.sub(r"[^a-z]", "", text)


def _to_decimal(cell: str):
    """Parse an AR-formatted number ('1.234,56') to Decimal, or None if empty."""
    cell = (cell or "").strip()
    if not cell or cell in {"-", "s/c", "S/C"}:
        return None
    cell = cell.replace(".", "").replace(",", ".")
    try:
        return Decimal(cell)
    except InvalidOperation:
        return None


class CanuelasConnector(BaseConnector):
    slug = "canuelas"

    def default_target_date(self, today: date) -> date:
        """One-day lag: yesterday's data is final, today's is provisional."""
        return today - timedelta(days=1)

    def fetch(self, *, target_date: date) -> bytes:  # pragma: no cover - network
        import urllib.request

        # NOTE: the date range form may require POST. Confirm the exact params
        # against the live site before relying on this in production.
        req = urllib.request.Request(BASE_URL, headers={"User-Agent": "alvs-feedlot/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()

    def parse(self, payload: bytes, *, target_date: date) -> list[ParsedPrice]:
        html = payload.decode("cp1252", errors="replace")

        if _PROVISIONAL in html.upper():
            # Provisional page: the day hasn't closed. Not an error — just no data yet.
            return []

        rows = self._extract_table_rows(html)
        if rows is None:
            # We are not on a provisional page (checked above) yet there is no price
            # table: the HTML changed. Fail loudly so the source gets looked at.
            raise ConnectorError("Cañuelas: no encuentro la tabla de precios (¿cambió el HTML?).")
        if not rows:
            return []

        # The header may be two stacked rows (Precios/Totales over Mínimo/Máximo/...).
        # Find the row that actually carries the labels and take the body after it.
        header_idx = self._find_header_row(rows)
        if header_idx is None:
            raise ConnectorError("Cañuelas: no encuentro la fila de encabezado (¿cambió el HTML?).")
        col_map = self._map_columns(rows[header_idx])
        body = rows[header_idx + 1:]
        if "category" not in col_map or "price_avg" not in col_map:
            raise ConnectorError("Cañuelas: no encuentro las columnas esperadas (¿cambió el HTML?).")

        parsed = []
        for cells in body:
            if len(cells) <= max(col_map.values()):
                continue
            category = cells[col_map["category"]].strip()
            if not category:
                continue
            avg = _to_decimal(cells[col_map["price_avg"]])
            if avg is None:
                continue  # a row without an average is a header/spacer, skip it
            price = ParsedPrice(category=category, date=target_date, price_avg=avg)
            for field_name in ("price_min", "price_max", "price_median"):
                if field_name in col_map:
                    setattr(price, field_name, _to_decimal(cells[col_map[field_name]]))
            if "head_count" in col_map:
                head = _to_decimal(cells[col_map["head_count"]])
                price.head_count = int(head) if head is not None else None
            price.raw = {"cells": cells}
            parsed.append(price)
        return parsed

    @staticmethod
    def _extract_table_rows(html: str) -> list[list[str]]:
        """Return the price table as a list of rows of cell-text. HTML-parser based."""
        from html.parser import HTMLParser

        class _TableReader(HTMLParser):
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

        reader = _TableReader()
        reader.feed(html)
        # The price table is the one whose header mentions "Categoria" and "Promedio".
        for table in reader.tables:
            flat = _norm(" ".join(" ".join(r) for r in table[:2]))
            if "categoria" in flat and "promedio" in flat:
                return table
        return None

    @staticmethod
    def _find_header_row(rows) -> int | None:
        """Index of the row carrying the column labels (has 'promedio' and 'minimo')."""
        for idx, row in enumerate(rows):
            keys = {_norm(c) for c in row}
            if "promedio" in keys and "minimo" in keys:
                return idx
        return None

    @staticmethod
    def _map_columns(header_row) -> dict:
        """Map our field names to column indexes from the labelled header row.

        'Categoría' may live in an earlier merged column; if it is not labelled we
        default it to column 0, which is where Cañuelas puts it.
        """
        col_map = {}
        for idx, cell in enumerate(header_row):
            key = _norm(cell)
            if key in _COLUMN_ALIASES:
                col_map[_COLUMN_ALIASES[key]] = idx
        col_map.setdefault("category", 0)
        return col_map
