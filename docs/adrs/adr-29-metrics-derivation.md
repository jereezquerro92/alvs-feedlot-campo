---
title: adr-29-metrics-derivation
type: adr
status: active
created: 2026-07-21
tags: [adr, feedlot, metrics, derivation, phase-3]
---

# ADR-29 — metric derivation and the "not calculable" contract

**Context:** consumes [[adr-25-account-ledger]] and [[adr-28-animal-lifecycle-and-sanitary]]; [[adr-27-advisors-generative]] will consume it.

## Context

The dashboard, the reports and the Phase 5 advisors need the same numbers. If each
computes them on its own, three consumers end up with three definitions of "feed
conversion" and none of them is the right one.

## Decisions

### 1. Metrics are derived in the backend, in a single app

`apps.metrics` has no models: it exposes pure functions over the operational events. The
frontend charts what it receives; it does not compute.

*Why:* a metric is a claim about the client's money and kilos. It has to be auditable,
testable and reproducible, and none of that is achieved in JavaScript inside the browser.
It also guarantees that the Phase 5 advisor and the chart the client looks at say the same
thing.

### 2. A metric that cannot be computed returns `null` and the reason

No function returns zero, a filler average or an estimate when data is missing. It returns
`null` together with a `not_calculable` field carrying the cause (`no_measured_growth`,
`no_weight_gain`, `no_intake_in_period`, …).

*Why:* a zero is charted exactly like a real zero. A feed conversion invented over a lot
with no weighings reads as a management figure and can justify a purchasing decision. The
explicit gap tells the operator what they have to go and measure; the invented number
tells them everything is already fine.

### 3. Growth is summed only over measurable segments

`kilos_gained` accumulates only the stretches between weighings whose ADG is calculable
(adr-28 rule 2), and reports how many stretches were skipped.

*Why:* without that counter there is no telling "the herd did not gain" from "we did not
measure it". They are opposite situations and the right answer to each is different.

### 4. Payments are not costs

`cost_breakdown` sums debits only. A payment is a credit and does not reduce the period's
cost; it reduces the balance.

*Why:* confusing them makes a client who pays look cheaper to feed. They are two distinct
questions: how much did it cost, and how much do they owe.

### 5. Inconsistencies are shown, not blocked

Recording a ration dated after the animal's death is allowed: late data entry is the norm
in the field. The dashboard flags it as an inconsistency so that someone looks.

*Why:* blocking the entry forces the operator to falsify the date in order to keep
working, and there the data is truly lost. Better to accept it and mark it.

## Consequences

- Every consumer of metrics must handle `null`. A frontend that assumes there is always a
  number will break, and it is right that it breaks in development and not in production.
- Aggregations walk events: at real volume, daily per-client summaries will have to be
  materialized. The functions' interface does not change when that happens, only their
  implementation.
