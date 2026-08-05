---
title: adr-34-pen-placement
type: adr
category: backend
use_case: move livestock between pens, read pen occupancy or head count, attribute an animal to a pen on a date
created: 2026-07-25
modified: 2026-08-04
tags: [adr, feedlot, feedyard, pens, placement, phase-7b]
---

# ADR-34 — Livestock placement in pens (`PenPlacement`)

## CONTEXT

> Where each animal is: the missing fact that lets a pen be something more than a label on the feeding. Recorded as a dated movement, with occupancy derived from those movements.

## ASSERTIONS

1. `PenPlacement` records a dated movement of an `Animal` or a `Lot` into (`direction=in`) or out of (`direction=out`) a `Pen`. Current location and occupancy are derived from those events and are never stored as an editable field on `Pen` or `Animal` ([[adr-24-feedlot-domain]] rule 3).
2. A `PenPlacement` points to an `Animal` or a `Lot`, never both and never neither: `CHECK` with two nullable FKs, identical to the lifecycle events ([[adr-26-livestock-individual-and-lot]] rule 3). For a lot, `head_count` allows moving a subset; an individual animal is not fractioned.
3. `PenPlacement` posts no ledger entry: moving livestock between pens is internal logistics, not a delivered input. Charging stays exclusively in `feed` ([[adr-25-account-ledger]] rule 4), as throughout `feedyard` ([[adr-33-feedyard-operating-loop]] rule 1).
4. `register_placement` rejects at the service layer —not at the view— a `Pen` with `status=inactive` and an `Animal` that is not `active`: dead, sold, or discharged animals cannot be placed. Late-entry with a backdated date is accepted as long as the pen remains active.
5. `apps.metrics` derives per pen the current head count, heads entering and leaving in the period, and kilos fed. Pen conversion is completed by [[adr-42-pen-conversion-honest-cut]], which uses these events to attribute weight gain.
6. `Pen` has no FK to client: a pen houses livestock from multiple clients, and it is the placement that links each head to its pen and —through the animal or lot— to its owner.

## FORBIDDEN

- **NEVER** store location as a mutable field on `Animal` or `Pen` (rule 1). A feedlot moves livestock constantly, and a field would lose which pen the animal came from and how long it was there.
- **NEVER** post a ledger entry for a pen movement (rule 3). Location is management information, not an economic fact.
- **NEVER** place an animal that is not active (rule 4). Dead, sold, or discharged animals do not occupy a pen.
- **NEVER** validate the pen or the animal in the view (rule 4). The rule lives in the service, the sole write point.
- **NEVER** link a pen to a client (rule 6). The pen belongs to the feedlot and houses livestock from multiple owners simultaneously.

## REJECTED

- **A mutable `Animal.pen` field** — location as state, simpler to read. Rejected by rule 1: it loses the entire history, which is precisely what makes the pen close auditable.
- **A polymorphic "livestock unit" table** — a single target for the placement. Rejected for the same reason as [[adr-26-livestock-individual-and-lot]] rule 3: indirection on every query in exchange for nothing.
- **Pen conversion in this phase** — closing gain alongside occupancy. Deferred for metric honesty and later resolved by [[adr-42-pen-conversion-honest-cut]], which attributes only clean intervals.

## RELATED

### related adrs

- [[docs/adrs/adr-33-feedyard-operating-loop]] — the phase that left the pen without placed livestock
- [[docs/adrs/adr-26-livestock-individual-and-lot]] — rule 3, the XOR this event reuses
- [[docs/adrs/adr-42-pen-conversion-honest-cut]] — what is derived from these movements
- [[docs/adrs/adr-29-metrics-derivation]] — the explicit gap instead of a fabricated number

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `PenPlacement` and `Pen`
- [[docs/API]] — the placement routes
