---
title: adr-39-gross-margin-and-fx
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, margins, fx, currency, metrics, phase-12]
---

# ADR-39 — derived gross margin and reference exchange rate

**Context:** closes the roadmap. Reuses the metrics of [[adr-29-metrics-derivation]] (one
single definition of each number) and the market price of
[[adr-30-market-prices-connectors]] as a reference value, and does not touch the ledger, which
stays in ARS at the historical price ([[adr-25-account-ledger]] rule 3). Grows by addition
([[adr-49-domain-layer-and-growth-by-addition]]). Rules only; the entities live in
[[FEEDLOT-DATA-MODEL]].

## Context

The system knows how much it cost to feed a client (`cost_breakdown`) and how many kilos it
produced (`kilos_gained`), but it never crossed the two into a **gross margin**: what the
production was worth minus what it cost. And everything is in ARS; a client who reasons in
dollars has nowhere to read a reference figure in USD. Two things are missing: the derived
**margin** and a reference **exchange rate** to express it in another currency.

## Decisions

### 1. The exchange rate is a reference series, not the account's currency

`FxRate` is a dated row per `(currency, date, source)` with the `rate` in ARS per one unit of
`currency` (e.g. USD→ARS). It is an external reference value, exactly like the cattle market
price (adr-30): it does **not** redenominate the ledger, which stays in ARS at the historical
price per entry ([[adr-25-account-ledger]] rule 3).

*Why:* the current account is a contract in pesos; converting it to dollars would change the
amount the client owes depending on the day it is looked at. The exchange rate expresses, it
does not redefine.

### 2. `FxRate` is idempotent by its triple and the rate is positive

Re-ingesting a `(currency, date, source)` updates the row, it does not duplicate it — the same
discipline as `MarketPrice` (adr-30 rule 6). `register_fx_rate` rejects a non-positive `rate`.
In this phase loading is manual (`source="manual"`); an automatic connector is a future
addition with its own change, not part of this cut.

*Why:* the source is the truth, the row is a cache of the last read. A zero or negative rate is
not an exchange rate, it is broken data.

### 3. The gross margin is derived in `apps.metrics`, with a single definition

`gross_margin` lives in `apps.metrics` (adr-29 rule 1), not in a new app: it is a metric, not a
model. It crosses `kilos_gained` × reference market price (revenue) against `cost_breakdown`
(cost, debits only, adr-29 rule 4). The advisor, the dashboard and this figure read the same
numbers because they are the same source.

*Why:* three consumers with three definitions of "margin" is what the metrics doctrine exists
to prevent. The only new model is `FxRate`; the margin is a pure function.

### 4. Each missing input returns `null` with its reason, never a filler

`gross_margin` returns `null` with `not_calculable` when any input is missing:
`no_measured_growth`/`no_weight_gain` (no measurable kilos, adr-29 rule 2),
`no_reference_price` (no market price for the category/source) or, when another currency is
requested, `no_fx_rate` (the ARS amount comes out all the same; only the conversion stays
`null`).

*Why:* a margin invented over a lot with no weighings reads as management and justifies a
purchase. The explicit gap says what is missing to measure; the invented number says everything
is already fine.

### 5. Revenue is a reference, not an entry

The margin's "revenue" is kilos produced × market price — a theoretical management value, not
money collected. It posts no `LedgerEntry`: the sale is the client's, not the feedlot's
([[adr-28-animal-lifecycle-and-sanitary]] rule 3). The margin informs; the ledger charges, and
they remain distinct things.

*Why:* a single charging path remains the ledger via `feed` (adr-25). Confusing a reference
margin with real revenue would reopen the door the doctrine closed.

## Consequences

- The backend enters only through [[API]] (adr-03) and is born through the [[TDD]] flow
  (adr-07).
- `FX_` adds no credentials: loading `FxRate` is manual in this phase, with no external
  service. A connector (BCRA or another) enters later with its own ADR, like those of adr-30.
- `apps.metrics` gains `gross_margin`; `apps.fx` contributes the only new model (`FxRate`) and
  its `register_fx_rate`/`latest_rate` services. `market`, `ledger` and `livestock` are not
  refactored.
- Any change to rules 1–5 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
