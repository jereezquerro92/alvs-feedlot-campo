---
title: adr-34-pen-placement
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, feedyard, pens, placement, phase-7b]
---

# ADR-34 — cattle placement in pens (`PenPlacement`)

**Context:** completes the deferral of [[adr-33-feedyard-operating-loop]] decision 7 (the
per-pen close needs to know which cattle were in the pen). Reuses the animal/lot XOR
constraint of [[adr-26-livestock-individual-and-lot]] and the event-sourced posture of
[[adr-49-domain-layer-and-growth-by-addition]]. Rules only; the entities live in
[[FEEDLOT-DATA-MODEL]].

## Context

Phase 7 gave the pen (`Pen`), the recipe (`Ration`), the plan (`LoadingOrder`) and the bunk
reading (`BunkScore`), but not where each animal is. Without that, the pen is a label on the
`FeedingEvent` and nothing more: there is no occupancy, no head per pen, no basis for a
per-pen close. The missing fact is added — **where the cattle are** — without touching how
charging works and without rewriting the stable domain.

## Decisions

### 1. Placement is an immutable event, not a state field

`PenPlacement` records a dated movement of an `Animal` or a `Lot` into (`direction=in`) or
out of (`direction=out`) a `Pen`. Current placement and occupancy are **derived** from those
events; they are never stored as an editable field on `Pen` or on `Animal` (the same posture
as adr-49 rule 3, adr-26 rule 4).

*Why:* a feedlot moves cattle between pens all the time. A mutable `Animal.pen` field would
lose the history — which pen it came from, how long it stayed. The event preserves it and
makes the per-pen close auditable.

### 2. Exactly one target, at the database level

A `PenPlacement` points to an `Animal` OR a `Lot`, never both and never neither — a `CHECK`
constraint with two nullable FKs, identical to the one on lifecycle events (adr-26 rule 3).
For an individual animal the movement is one head; for a lot, `head_count` allows moving a
part.

*Why:* reusing the already-proven shape avoids a polymorphic table and keeps the query
direct. A lot is moved partially in practice; an animal is not fractioned.

### 3. It does not touch the ledger

`PenPlacement` posts no entry. Moving cattle between pens is neither an input delivered nor
a charge — it is internal logistics. Charging stays exclusively in `feed` (adr-25 rule 4),
like all the rest of `feedyard` (adr-33 decision 1).

*Why:* a single charging path. Placement is management information, not an economic fact.

### 4. An inactive pen and a non-active animal reject the entry, in the service

`register_placement` rejects, in the **service** (not in the view), a `Pen` with
`status=inactive` and an `Animal` that is not `active` (dead/sold/departed is not placed).
Late entry with a retroactive date is accepted while the pen is still active — the same rule
as adr-28 for weighings and sanitary events.

*Why:* business rules live in the service, the single write point, so that the view, the
admin and a command share the same validation.

### 5. This phase's per-pen close is occupancy, not gain

`apps.metrics` gains a per-pen report: current occupancy (head), head in/out in the period
and kilos fed to the pen. **Per-pen conversion** (kg produced ÷ kg fed) stays deferred:
attributing weighings to the stretch an animal spent in a pen is a separate problem, and a
number without that attribution would be invented (adr-29 rule 2). What is affirmable today
is delivered; per-pen conversion enters when the attribution exists.

*Why:* metric honesty. Occupancy can be affirmed from the placement events; per-pen
conversion cannot, yet.

## Consequences

- The backend enters only through [[API]] (adr-03) and is born through the [[TDD]] flow
  (adr-07).
- The only migration is the new `PenPlacement` table in `feedyard`; nothing outside the app,
  nothing in `ledger`.
- `Pen` still has no client FK: a pen may host cattle from several clients, and it is the
  placement that ties each head to its pen and its owner (via the animal/lot).
- Any change to rules 1–5 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
