---
title: adr-26-livestock-individual-and-lot
type: adr
status: proposed
created: 2026-07-21
tags: [adr, feedlot, livestock]
---

# ADR-26 — cattle are tracked as individuals and as lots

Rules only; content lives in [[FEEDLOT-DATA-MODEL]].

1. Cattle enter through an `Intake` event with `mode` ∈ {`individual`, `lot`}.
   `individual` creates one `Animal` per ear tag; `lot` creates or updates a `Lot` carried
   as `head_count` + `total_weight` with no per-head identity. Both modes are first-class;
   neither is a workaround for the other.
2. An `Animal` MAY belong to a `Lot` (`Lot.mode=named`) or stand alone. A `Lot.mode=anonymous`
   holds only counts and weight and references no `Animal`. A lot may be nominated later;
   an animal is never silently absorbed into an anonymous lot's counters.
3. The events `Weighing`, `Death`, `Exit` target an `Animal` OR a `Lot` — never both and
   never neither. This is enforced at the database level: two nullable FKs (`animal`, `lot`)
   plus a CHECK constraint that exactly one is set. A polymorphic "livestock unit" table was
   considered and rejected for its indirection; the dual-nullable-FK shape is the standing
   choice for its explicitness and queryability.
4. Lot counters (`head_count`, `total_weight`) are maintained only by events: `Intake` adds,
   `Death`/`Exit` subtract (by their `head_count`/`weight` for partial lot operations),
   `Weighing` corrects `total_weight`. They are never hand-edited — consistent with the
   event-sourced posture ([[adr-24-feedlot-domain]] rule 3).
5. `Animal.current_weight` is derived from the latest `Weighing`; growth metrics (daily gain,
   lot average, feed conversion) are derived across successive `Weighing` rows and are never
   stored as editable fields.
6. Categories, sex and status are English `choices` ([[LOCALIZATION]]); Spanish labels exist
   only in rendered frontend output.
