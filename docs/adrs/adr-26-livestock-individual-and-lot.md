---
title: adr-26-livestock-individual-and-lot
type: adr
category: backend
use_case: registering an intake, writing an event that targets cattle, adding a field to Animal or Lot, deriving a weight or a growth metric
created: 2026-07-21
modified: 2026-08-02
tags: [adr, feedlot, livestock]
---

# ADR-26 — cattle are tracked as individuals and as lots

## CONTEXT

> Cattle arrive either as identified animals or as a lot carried by head count and total weight. Both are first-class, every event targets exactly one of them, and the database is what enforces the "exactly one".

## ASSERTIONS

1. Cattle enter through an `Intake` with `mode` ∈ {`individual`, `lot`}. `individual` creates one `Animal` per ear tag; `lot` creates or updates a `Lot` carried as `head_count` and `total_weight`, with no per-head identity. Neither mode is a workaround for the other.
2. An `Animal` may belong to a `Lot` (`Lot.mode=named`) or stand alone. A `Lot.mode=anonymous` holds counts and weight and references no `Animal`. A lot may be nominated later; an animal is never absorbed into an anonymous lot's counters.
3. `Weighing`, `Death` and `Exit` target an `Animal` or a `Lot` — never both, never neither — enforced in the database by two nullable foreign keys and a `CHECK` constraint that exactly one is set.
4. Lot counters are maintained only by events: `Intake` adds, `Death` and `Exit` subtract by their own `head_count` or `weight` for partial operations, `Weighing` corrects `total_weight`. They are never hand-edited ([[adr-24-feedlot-domain]] rule 3).
5. `Animal.current_weight` is derived from the latest `Weighing`; growth metrics — daily gain, lot average, feed conversion — are derived across successive weighings and never stored as editable fields.
6. Categories, sex and status are English `choices` ([[LOCALIZATION]]); Spanish labels exist only in rendered frontend output.

## FORBIDDEN

- **NEVER** hand-edit a lot counter (rule 4). The counters are what the events say; edited, they stop being a record of anything.
- **NEVER** write an event with both targets set or neither (rule 3). The constraint rejects it, and code that tries is code that lost track of what it is weighing.
- **NEVER** store a derived weight or growth figure as an editable field (rule 5). It goes stale against the weighings the moment one is loaded late.
- **NEVER** fold an `Animal` into an anonymous lot's counters (rule 2). The animal has an identity that the counters cannot carry, and it would be counted twice.
- **NEVER** write a `choices` value in Spanish (rule 6). The value is code; the label is render.

## REJECTED

- **A polymorphic "livestock unit" table** — one table both `Animal` and `Lot` point at, so every event has a single target. Rejected for the indirection it puts in front of every query; the dual nullable FK plus `CHECK` is more explicit and directly queryable, and it is now the shape every lifecycle and reproductive event reuses.
- **Lot-only or individual-only tracking** — picking one mode and expressing the other through it. Rejected because each becomes a lie about the operation: an anonymous lot cannot carry an ear tag, and one `Animal` per head is a fiction when nobody identified them at the gate.

## RELATED

### related adrs

- [[docs/adrs/adr-24-feedlot-domain]] — rule 3, the event-sourced posture these counters follow
- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — rule 1, the abstract that carries this XOR
- [[docs/adrs/adr-34-pen-placement]] — the same XOR applied to placement
- [[docs/adrs/adr-46-breeding-reproduction]] — the same XOR applied to the reproductive events

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `Animal`, `Lot`, `Intake` and their fields
- [[docs/LOCALIZATION]] — English in code, Spanish only in render
