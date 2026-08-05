---
title: adr-42-pen-conversion-honest-cut
type: adr
category: backend
use_case: read or change the per-pen conversion, attribute gain to a pen, compose the pen closeout
created: 2026-07-25
modified: 2026-08-04
tags: [adr, feedlot, feedyard, metrics, conversion, pen, phase-4b]
---

# ADR-42 — Per-Pen Conversion: the Honest Cut

## CONTEXT

> The gain half of the pen closeout, which was deferred because a kilo of weight gain carries no record of which pen it was produced in. With `PenPlacement` the honest subset is attributed —the segments the animal spent entirely in one pen— and the ambiguous portion is declared non-calculable.

## ASSERTIONS

1. `pen_conversion(*, pen, start, end)` is a pure function in `apps.metrics`, sibling of `pen_occupancy_report` and `pen_cost_summary`. There is no table or migration: conversion is a derived assertion, not a stored datum ([[adr-29-metrics-derivation]] rule 1).
2. A weighing segment is attributed to the pen where the target was at the previous weighing, and only if no `PenPlacement` occurred strictly inside the interval and that pen is the one being measured. The location is derived from the `in`/`out` events ([[adr-34-pen-placement]] rule 1): an `in` fixes the pen, an `out` releases it.
3. The non-attributable is counted. A segment whose ADG is already non-calculable ([[adr-28-animal-lifecycle-and-sanitary]] rule 2) is skipped (`segments_skipped`); a calculable one that cannot be fixed to a single stay —the animal changed pens, or the target has no placement here— counts as `segments_unattributed`. Kilos are summed only over `segments_attributed`.
4. `pen_conversion` returns `null` with its `not_calculable` when there is no attributable segment (`no_attributable_growth`), when the attributed gain came out flat or negative (`no_weight_gain`), or when no feed is recorded for the pen in the period (`no_feed_recorded`). Never a filler zero.
5. It is pure read: it posts no ledger entry, mutates nothing, and adds no variables or endpoints in this cut. It is delivered as a tested service function, with the same exposure as its siblings, until a pen dashboard exists to consume them.
6. `pen_closeout(*, pen, start, end)` composes the occupancy half with the conversion half into a single pen closeout, and each half carries its own `not_calculable`. The per-client conversion does not change: this metric is its disaggregation by pen.

## FORBIDDEN

- **NEVER** attribute to a pen a segment in which the animal changed pens (rule 2). The gain was distributed in a way the data do not record, and assigning all of it to one pen is the fabricated number that [[adr-29-metrics-derivation]] rule 2 prohibits.
- **NEVER** return zero when there is nothing attributable (rule 4). A zero charts the same as a real zero and can justify a purchasing decision.
- **NEVER** omit the segment counters (rule 3). Without them, "the pen did not gain weight" cannot be distinguished from "we could not attribute the gain to it".
- **NEVER** store the conversion as a datum (rule 1). It becomes stale with the next weighing and creates a second definition of the number.

## REJECTED

- **Prorating gain across pens** — splitting the broken segment by days in each pen. Rejected: the proportion is not in the data, so the split would be an estimate presented as a measurement.
- **Attributing the segment to the pen of the final weighing** — a simple rule to avoid losing segments. Rejected against rule 2: it gifts to a pen the gain that another pen produced.
- **Exposing an endpoint for this metric alone** — publishing it before its two siblings. Rejected for asymmetry and for adding a route with no consumer; all three are exposed together when the dashboard that uses them exists.

## RELATED

### related adrs

- [[docs/adrs/adr-34-pen-placement]] — rule 1, the events that make attribution possible
- [[docs/adrs/adr-33-feedyard-operating-loop]] — the cost half of the pen closeout
- [[docs/adrs/adr-29-metrics-derivation]] — rules 1 to 3, derive not invent, and count the skipped
- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — rule 2, the non-calculable ADG

### related files

- [[docs/FEEDLOT]] — the pen closeout in operation
- [[docs/FEEDLOT-DATA-MODEL]] — `PenPlacement`, `Weighing`, `FeedingEvent`
