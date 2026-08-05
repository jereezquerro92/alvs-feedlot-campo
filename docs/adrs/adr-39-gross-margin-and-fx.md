---
title: adr-39-gross-margin-and-fx
type: adr
category: backend
use_case: read or change the gross margin, load an exchange rate, express a figure in another currency
created: 2026-07-25
modified: 2026-08-04
tags: [adr, feedlot, margins, fx, currency, metrics, phase-12]
---

# ADR-39 — Derived Gross Margin and Reference Exchange Rate

## CONTEXT

> Crossing what it cost against what the output was worth, and being able to express it in another currency. The margin is a derived function and the exchange rate a reference series: neither redenominates the account nor posts a ledger entry.

## ASSERTIONS

1. `FxRate` is a row dated by `(currency, date, source)` with the `rate` in ARS per unit of `currency`. It is an external reference value, like the market price ([[adr-30-market-prices-connectors]]): it does not redenominate the ledger, which remains in ARS with historical price per entry ([[adr-25-account-ledger]] rule 3).
2. `FxRate` is idempotent by its triplet —re-ingesting updates the row, not duplicating it— and `register_fx_rate` rejects a non-positive `rate`. Loading is manual (`source="manual"`); an automatic connector enters with its own change.
3. `gross_margin` lives in `apps.metrics` ([[adr-29-metrics-derivation]] rule 1), not in a new app: it is a metric, not a model. It crosses `kilos_gained` × reference market price against `cost_breakdown`, which sums only debits ([[adr-29-metrics-derivation]] rule 4).
4. `gross_margin` returns `null` with its `not_calculable` when any input is missing: `no_measured_growth` or `no_weight_gain` without measurable kilos, `no_reference_price` without a price for the category or source, and `no_fx_rate` when another currency is requested —in that last case the ARS amount still comes out and only the conversion is `null`.
5. The margin's revenue figure is a theoretical management value —kilos produced × market price—, not money received, and it posts no `LedgerEntry`. The only output that does settle is the sale, governed by [[adr-43-sale-settlement]].
6. `apps.fx` provides the only new model with its services `register_fx_rate` and `latest_rate`; `market`, `ledger`, and `livestock` are not refactored. No credentials are added.

## FORBIDDEN

- **NEVER** redenominate the account with an exchange rate (rule 1). The current account is a contract in pesos, and converting it would change what the client owes depending on the day it is viewed.
- **NEVER** post a ledger entry for the margin's theoretical revenue (rule 5). Confusing a reference margin with money received reopens the door the doctrine closed.
- **NEVER** return a filler margin when an input is missing (rule 4). A fabricated margin on a lot with no weighings reads as management data and can justify a purchase.
- **NEVER** store a zero or negative `rate` (rule 2). It is not an exchange rate, it is broken data.
- **NEVER** define the margin outside `apps.metrics` (rule 3). Three consumers with three definitions of "margin" is precisely what the metrics doctrine exists to prevent.

## REJECTED

- **Keeping the account in dual currency** — entries converted to USD alongside the peso amount. Rejected by rule 1: the balance would then depend on the day it is viewed.
- **An automatic exchange-rate connector in this cut** — BCRA or another source ingested like the prices. Explicitly deferred; enters with its own change, following the pattern of [[adr-30-market-prices-connectors]].
- **A dedicated app for the margin** — `margins`, with its model and rows. Rejected by rule 3: the margin is a pure function over events, and storing it would make it stale the next day.

## RELATED

### related adrs

- [[docs/adrs/adr-29-metrics-derivation]] — rules 1, 2, and 4, where the number lives and what it returns without inputs
- [[docs/adrs/adr-30-market-prices-connectors]] — the reference price and the idempotent discipline
- [[docs/adrs/adr-25-account-ledger]] — rule 3, the account in ARS with historical price
- [[docs/adrs/adr-43-sale-settlement]] — the sale, which does settle

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `FxRate`
- [[docs/API]] — the margin and exchange-rate routes
