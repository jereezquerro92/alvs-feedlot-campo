---
title: adr-30-market-prices-connectors
type: adr
category: backend
use_case: write or fix a price connector, ingest a date, choose a reference source, test a parser against a fixture
created: 2026-07-23
modified: 2026-08-04
tags: [adr, feedlot, market, prices, connectors]
---

# ADR-30 — Reference prices and source connectors

## CONTEXT

> Livestock prices are an external market reference value: they are not the account's currency, which remains in ARS at historical cost. Each source enters through a connector that separates networking from parsing and fails in a distinguishable way.

## ASSERTIONS

1. Cañuelas is the primary daily source and datos.gob.ar is discarded: its official novillo series ended in 2019, verified against the live site.
2. IPCVA is the second automatic source — server-rendered pages, monthly redundancy from an independent provider — and ROSGAN remains a manual-entry source, because it builds its table with JavaScript and publishes periodic auctions, not a daily price.
3. Each connector separates `fetch` (brings bytes, uses the network) from `parse` (interprets, pure). Tests target `parse` against a fixed fixture, never the live site.
4. The parser maps columns by reading the header row, never by position. If the site reorders columns, values do not slip to the wrong field, and if the header disappears it fails instead of saving garbage.
5. Three states are distinguished: provisional page for the current day → empty, not an error; table present with no rows (day with no operations) → empty; table absent (the HTML changed) → `ConnectorError`.
6. Ingestion is idempotent by `(source, category, date)`: re-ingesting updates the row, not duplicates it. The raw payload is saved in `raw` to redo parsing without re-fetching.
7. A failed source does not stop the others: `ingest_prices` isolates each one, records the failure, and continues. When there is a gap, `latest_price` returns the last known value.
8. Two automatic sources are never averaged. Cañuelas is a daily physical market price in ARS and IPCVA is a monthly index in USD/kg: they measure different things with different lag, are stored separately by their `source`, and the consumer chooses.
9. `MarketPrice` stores minimum, maximum, average, median, and head count, not just the average, because the sources publish them and the advisor can use them.

## FORBIDDEN

- **NEVER** average two sources (rule 8). That would fabricate a number no source publishes, and with different units it is not even an average.
- **NEVER** map columns by position (rule 4). A reordering of the site saves prices in the wrong field without failing.
- **NEVER** confuse "no operations took place" with "the HTML changed" (rule 5). The second case would go unnoticed for days reading as a quiet market.
- **NEVER** test a parser against the live site (rule 3). The site goes down and changes, and the test would stop telling whether the parser is correct.
- **NEVER** hide a connector failure with a silent `try/except` (rule 7). Per-source isolation exists to record the failure, not to hide it.

## REJECTED

- **datos.gob.ar as the primary source** — the strategy assumed by document 06. Dropped on verification: the official novillo series ends in 2019. Would reopen only if the agency resumed it.
- **ROSGAN as an automatic source** — discarded due to site construction: JavaScript builds the table and what it publishes are periodic auctions, not a daily price. Remains as a manual-entry index.
- **Averaging Cañuelas and IPCVA into a single price** — one reference number, more convenient for the dashboard. Rejected by rule 8; consumer convenience does not justify inventing the series.

## RELATED

### related adrs

- [[docs/adrs/adr-25-account-ledger]] — rule 3, why the account is not redenominated with these prices
- [[docs/adrs/adr-39-gross-margin-and-fx]] — the margin that consumes this reference price
- [[docs/adrs/adr-29-metrics-derivation]] — the gap contract that `latest_price` respects

### related files

- [[docs/feedlot/06-precios-hacienda]] — the sources, their URLs, and their forms
- [[docs/feedlot/06b-verificacion-fuentes-precios]] — the verification against the live sites
- [[docs/feedlot/06c-segunda-fuente-automatica]] — IPCVA, its series, and its unit caveat
- [[docs/FEEDLOT-DATA-MODEL]] — `MarketPrice` and `MarketSource`
