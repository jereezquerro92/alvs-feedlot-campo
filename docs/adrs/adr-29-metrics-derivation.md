---
title: adr-29-metrics-derivation
type: adr
category: backend
use_case: add or change a metric, graph a number in the frontend, decide what to return when data is missing, read costs or growth for a client
created: 2026-07-21
modified: 2026-08-04
tags: [adr, feedlot, metrics, derivation, phase-3]
---

# ADR-29 — Metrics derivation and the "not calculable" contract

## CONTEXT

> Every business number is defined once, in the backend, as a pure function over events. When inputs are missing the function returns `null` with the reason, never a filler zero.

## ASSERTIONS

1. Metrics are derived in `apps.metrics`, which has no models: it exposes pure functions over the operational events. The frontend graphs what it receives and does not calculate. A single definition of each number, shared by the dashboard, reports, and advisors.
2. A metric without inputs returns `null` alongside a `not_calculable` field with the cause (`no_measured_growth`, `no_weight_gain`, `no_intake_in_period`, …). Never a zero, a filler average, or an estimate.
3. `kilos_gained` accumulates only the segments between weighings whose ADG is calculable ([[adr-28-animal-lifecycle-and-sanitary]] rule 2), and reports how many segments were skipped: without that counter there is no way to distinguish "the herd did not gain weight" from "we did not measure it".
4. `cost_breakdown` sums only debits. A payment is a credit: it does not reduce the period's cost, it reduces the balance. How much it cost and how much is owed are two different questions.
5. Inconsistencies are shown, not blocked. Loading a ration dated after an animal's death is allowed — late entry is the norm in the field — and the dashboard flags it for someone to review.
6. Every metrics consumer handles `null`. A frontend that assumes a number always breaks, and it is correct that it breaks in development.

## FORBIDDEN

- **NEVER** calculate a metric in the frontend (rule 1). A metric is an assertion about the client's money and kilos, and in the browser it is neither auditable nor testable.
- **NEVER** return zero when an input is missing (rule 2). A zero graphs the same as a real zero and tells the operator everything is fine.
- **NEVER** estimate against a theoretical weight to fill a gap (rules 2–3). The number comes out plausible and false, which is worse than not coming out at all.
- **NEVER** subtract a payment from cost (rule 4). It makes a paying client appear cheaper to feed.
- **NEVER** block an entry for being inconsistent (rule 5). The operator falsifies the date to keep working and then the data is truly lost.

## REJECTED

- **Calculating metrics in each consumer** — the dashboard, the report, and the advisor each with their own formula. That is exactly the problem this ADR exists to close: three definitions of "feed conversion" and none correct.
- **Materializing daily summaries per client from the start** — aggregate tables instead of scanning events. Deferred, not discarded: with real volume it will be needed, and the function interface does not change when that happens, only its implementation.
- **Blocking late or inconsistent entries** — validate against the death date and reject. Lost to rule 5: falsified data is worse than uncomfortable data.

## RELATED

### related adrs

- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — rule 2, the non-calculable ADG that rule 3 accumulates
- [[docs/adrs/adr-25-account-ledger]] — the entries that rule 4 sums
- [[docs/adrs/adr-27-advisors-generative]] — the generative consumer of these numbers
- [[docs/adrs/adr-42-pen-conversion-honest-cut]] — the same honest cut, by pen
- [[docs/adrs/adr-39-gross-margin-and-fx]] — the margin derived over these functions

### related files

- [[docs/FEEDLOT]] — what each number means in the operation
- [[docs/FEEDLOT-DATA-MODEL]] — the events over which derivation runs
- [[docs/API]] — the metrics routes
