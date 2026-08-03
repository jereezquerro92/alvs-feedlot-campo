---
title: adr-30-market-prices-connectors
type: adr
status: active
created: 2026-07-23
tags: [adr, feedlot, market, prices, connectors, phase-4]
---

# ADR-30 — reference prices and source connectors

**Context:** implements [[06-precios-hacienda]] with the corrections of [[06b-verificacion-fuentes-precios]] and [[06c-segunda-fuente-automatica]].

## Context

The system needs reference cattle prices for metrics and for the finance advisor. They
are not the account's currency — that stays in ARS at the historical price — but an
external market value. Document 06 assumed sources that, once verified, turned out to be
different from what was expected.

## Decisions

### 1. Cañuelas is the primary source, not datos.gob.ar

The official steer series on datos.gob.ar ended in 2019 (verified). The Mercado
Agroganadero de Cañuelas publishes daily prices by category and is alive. Document 06's
strategy is inverted: Cañuelas primary, datos.gob.ar discarded.

### 2. IPCVA is the second automatic source; ROSGAN stays manual

IPCVA serves server-rendered pages (scrapeable); ROSGAN builds its table with JavaScript
and publishes periodic auctions, not a daily price. IPCVA gives monthly redundancy from an
independent provider; ROSGAN stays as a manually loaded index. Detail in
[[06c-segunda-fuente-automatica]].

### 3. `fetch` and `parse` are separate steps

Every connector separates fetching the bytes (`fetch`, with network) from interpreting
them (`parse`, pure). The parser is therefore tested against a fixed fixture without
depending on the real site, which goes down and changes. The tests target `parse`.

### 4. The parser reads the header to map columns

The Cañuelas connector does not assume the column order: it reads the header row and maps
name→index. If the site reorders columns, values do not silently slide into the wrong
field; and if the header disappears, it fails with an error instead of storing garbage.

### 5. Three distinct states, three distinct responses

- **Provisional page** (same day, data not closed) → returns empty, not an error.
- **Table present with no rows** (a day with no trading) → returns empty.
- **Table absent** (the HTML changed) → `ConnectorError`.

Confusing them would make a change to the website read as "there were no prices" and go
unnoticed for days.

### 6. Idempotent ingestion by (source, category, date)

Re-ingesting a date updates the row, it does not duplicate it. The same discipline as the
rest of the system: the source is the truth, the row is a cache of the last read. The raw
payload is stored in `raw` so the parse can be redone without fetching again.

### 7. One source failing does not stop the others

The `ingest_prices` command isolates each source: if one goes down or changed its HTML, it
logs that and carries on with the others. No metric depends on an external source always
being up; when there is a gap, `latest_price` returns the last known value.

### 8. Two automatic sources are not averaged

Cañuelas (daily, physical market) and IPCVA (monthly, index) measure different things with
different lag. They will differ. The system stores both with their `source` and lets the
dashboard or the advisor choose according to the use. Averaging them would manufacture a
number that no source publishes.

## Integration points — resolved against the live site

The two that were still open were closed by verifying the real site (2026-07):

1. **Cañuelas — the date form.** Confirmed: the report is handled by a POST to the same
   URL (`hacienda1.dll/haciinfo000502`) with `txtFechaIni`/`txtFechaFin` in `DD/MM/YYYY`
   plus hidden fields. A bare GET returns the current day, still provisional. `fetch`
   posts the closed day; the POST is isolated in `build_form` (pure, tested) because
   `fetch` is network. Verified live: 22/07 → 18 rows, 21/07 → 19 rows, a day with no
   trading → 0 rows.
2. **IPCVA — the data endpoint.** Corrected: "Precios en Pie" is NOT a chart builder — it
   is `vista_precios.php?id=1`, a server-rendered HTML table (the earlier path
   `vista_precios2.php` was the different international view). `fetch` posts a range
   (`mes_desde`/`ano_desde`/`mes_hasta`/`ano_hasta` + `categorias[]`/`paises[]`) and
   `parse` reads the table, mapping columns by their header (rule 4). **Unit caveat:**
   this series is the **international** Novillos index **in USD/kg**, not ARS like
   Cañuelas — different by design, separated by `source` and never averaged with Cañuelas
   (rule 8). Every row records `currency: "USD"` in `raw`. The test runs against
   `fixture_ipcva.html`, a real page of the Novillos/Argentina series (Jan–Jun 2025).

## Consequences

- The Cañuelas scraper is the only automatic daily path: it needs real monitoring (an
  alert on N empty days or on out-of-range values), not a silent `try/except`. Per-source
  isolation enables it; the alert is added when it is operated.
- The `MarketPrice` model stores min/max/average/median/head, not only the average,
  because the sources give them and the advisor might use them.
