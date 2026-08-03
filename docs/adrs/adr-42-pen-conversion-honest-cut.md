---
title: adr-42-pen-conversion-honest-cut
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, feedyard, metrics, conversion, pen, phase-4b]
---

# ADR-42 — per-pen conversion: the honest cut

**Context:** lifts the explicit deferral of [[adr-33-feedyard-operating-loop]] decision 7 and
[[adr-34-pen-placement]] decision 5 (per-pen conversion stayed deferred because "attributing
weighings to the stretch an animal spent in a pen is a separate problem"). Consumes
`PenPlacement` (adr-34), `growth_series` ([[adr-28-animal-lifecycle-and-sanitary]]) and
`FeedingEvent.pen` (adr-33 decision 3). It is an **addition** to `apps.metrics`, not a
supersession: the rule forbidding the invented number ([[adr-29-metrics-derivation]] rule 2)
stays intact — this cut complies with it, it does not relax it. Rules only; the functions live
in `apps.metrics`.

## Context

The per-pen close had two halves. The **cost** half (kilos served and feed cost per pen) was
already delivered as `pen_cost_summary`/`pen_occupancy_report`: it derives from
`FeedingEvent.pen` and from the `PenPlacement` events, and it is affirmable. The **gain** half
— conversion = kg fed ÷ kg produced in the pen — was deferred because a kilo of gain does not
know which pen it was put on: attributing it without knowing where the animal was manufactures
the number adr-29 rule 2 forbids.

The missing piece — `PenPlacement`, where each head was and when — has existed since Phase 7b.
With it, **the honest subset** can be attributed: the weighing stretches an animal or lot spent
entirely within a single stay in a pen. What is ambiguous is declared not calculable, exactly
like everything else in the system.

## Decisions

### 1. Per-pen conversion is derived in `apps.metrics`, with no new model

`pen_conversion(*, pen, start, end)` is a pure function over events, sibling to
`pen_occupancy_report` (adr-34) and `pen_cost_summary` (adr-33). There is no table and no
migration: conversion is a derived claim, not stored data ([[adr-29-metrics-derivation]] rule
1). One single definition of the number, the same one the dashboard and the advisor will
consume.

*Why:* three consumers with three definitions of "per-pen conversion" is what the metrics
doctrine exists to prevent.

### 2. A kilo of gain is attributed to a pen only if the whole stretch was spent there

A weighing stretch (between two consecutive weighings of an animal or lot) is attributed to the
pen where the target was **at the previous weighing**, and **only if** there was no
`PenPlacement` event strictly inside the interval — that is, it did not change pen in between —
and that pen is the one being measured. Placement is derived from `PenPlacement`'s `in`/`out`
events (adr-34 decision 1): an `in` sets the pen, an `out` releases it.

*Why:* if the animal changed pen between two weighings, that stretch's gain was split across
pens in a way the data does not record. Attributing it whole to any one of them is exactly the
invented number of adr-29 rule 2. A clean stretch can be affirmed; a split one cannot.

### 3. What is not attributable is counted and reported, not filled in

A stretch whose ADG is already not calculable (adr-28 rule 2: same day, or the lot's
`head_count` changed) is **skipped** (`segments_skipped`). A calculable stretch that cannot be
pinned to a single stay in the pen — because it changed pen, or because the target has no
placement putting it here — is counted as **unattributed** (`segments_unattributed`). Kilos are
summed only over the **attributed** stretches (`segments_attributed`).

*Why:* without those counters there is no telling "the pen did not gain" from "we could not
attribute the gain to it". They are opposite situations and the right answer to each is
different — the same logic `kilos_gained` already applies with `segments_skipped` (adr-29 rule
3).

### 4. With nothing honest to divide, it returns `null` with the reason

`pen_conversion` returns `conversion=None` with a `not_calculable` when there is no attributable
stretch (`no_attributable_growth`), when the attributed gain came out flat or negative
(`no_weight_gain`), or when no feed was recorded to the pen in the period (`no_feed_recorded`).
Never a filler zero: a zero is charted exactly like a real zero
([[adr-29-metrics-derivation]] rule 2).

*Why:* an invented conversion over a pen with no attributable weighings reads as a management
figure and can justify a purchasing decision. The explicit gap tells the operator what is
missing to measure.

### 5. It touches neither the ledger nor any other app

`pen_conversion` is a pure read: it posts no entry, mutates nothing, and adds no environment
variables and no endpoints in this cut. It is delivered as a tested service function, with the
same exposure as its siblings `pen_occupancy_report`/`pen_cost_summary` — service-only until a
pen dashboard exists to consume them, which is a later addition through
[[adr-07-development-flow]] and [[API]].

*Why:* charging remains exclusively the ledger's via `feed` (adr-25). Exposing an endpoint for
only one of the three pen metrics, with no frontend using it, would be asymmetric and would add
a route with no consumer.

## Consequences

- The backend enters through the [[TDD]] flow (adr-07); the tests run at service level, just
  like `test_placement.py`.
- `pen_closeout(*, pen, start, end)` composes the occupancy half (`pen_occupancy_report`) with
  the conversion half (`pen_conversion`) into a single honest per-pen close; each half carries
  its own `not_calculable`.
- **Per-client** conversion (`conversion`, adr-29) does not change: it remains the client's
  total. This metric is its per-pen breakdown, with the honest gap where the attribution does
  not reach.
- Any change to rules 1–4 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
