---
title: adr-28-animal-lifecycle-and-sanitary
type: adr
status: active
created: 2026-07-21
tags: [adr, feedlot, livestock, sanitary, lifecycle, phase-2]
---

# ADR-28 — the animal lifecycle and the `sanitary` app

**Context:** extends [[adr-49-domain-layer-and-growth-by-addition]], [[adr-25-account-ledger]] and [[adr-26-livestock-individual-and-lot]].

## Context

Phase 1 left the animal entering the system and eating, but with no way to record
what happened to it afterwards: how much it gained, whether it died, when it left, or
what health treatment it received. Without that there is no traceability and no feed
conversion — the metric that justifies the system.

## Decisions

### 1. Lifecycle events share a shape, not a table

`Weighing`, `Death` and `Exit` inherit from an abstract `LifecycleEvent` model that
supplies the `animal`/`lot` pair and the XOR constraint of [[adr-26-livestock-individual-and-lot]].
Each keeps its own table.

*Why:* all three need "exactly one target" identically, and a single polymorphic event
table forces nullable fields everywhere and a filter by type on every query. The abstract
model keeps the three constraints from drifting apart without merging distinct domains.

### 2. Lot ADG is computed per head, and declared not calculable when the herd changes

Between two weighings of a lot, the compared weight is `total_weight / head_count`.
If `head_count` differs between the two weighings, the period is reported with
`adg = null` and `not_calculable = "head_count_changed"`.

*Why:* a lot's total moves through intakes, deaths and exits, not only through weight
gain. An ADG computed over the total measures anything but growth. The alternative —
estimating against a theoretical weight — produces a plausible and false number; an
explicit gap is preferable to a figure nobody can audit.

### 3. Deaths do not touch the ledger; the sale-exit is settled by [[adr-43-sale-settlement]]

A **death** (`Death`) posts no entry: the feed and health inputs already consumed stay
charged, and a death does not reverse them. An **exit** (`Exit`) does not reverse those
charges either; and in its `transfer`/`other` kind (withdrawal without sale) it still
posts nothing. The **sale-exit** (`Exit.kind=sale`) **does settle**, under the commercial
model the owner set and which [[adr-43-sale-settlement]] rules: a client's cattle
(`kind=boarding`) is charged a fattening commission (a service debit); own cattle
(`kind=own`) records the proceeds as a credit in the own account. The exit's
`sale_price_per_kg` stopped being merely informative: it is the price the settlement
snapshots ([[adr-25-account-ledger]] rule 3).

*Why:* the ledger charges inputs delivered, and that is why a death does not reverse
charges — doing so would turn the feedlot into the client's insurer, a commercial
decision and not a technical one; if it is ever taken, it enters as an explicit and
auditable `adjustment`, not as an automatic side effect. The sale is different: the owner
defined that boarding charges for the fattening and that own cattle produces its own
income, and that settlement arrives as its own ADR ([[adr-25-account-ledger]] rule 6),
without mutating any existing entry.

### 4. The app is called `sanitary`, not `health`

The template already uses `apps.health` for the liveness probe (`/api/health/`).

*Why:* a name collision. The new domain is renamed, not the existing infrastructure,
because the probe is a contract with the orchestrator. The earlier documentation
(`02-modelo-de-datos.md`, `07-arquitectura-escalable-y-roadmap.md`) mentions `health`
and is out of date on that point.

### 5. Every health application is charged

`register_health_event` always posts a debit. There is no equivalent to feeding's
`origin = client_stock`.

*Why:* health products are always supplied by the feedlot. Modelling an origin that is
never used is speculative complexity. If a client brings their own vaccine tomorrow, the
field is added then.

### 6. No health stock is tracked in this phase

Applications are recorded, not holdings. The `FeedStockMovement` pattern is available to
replicate if it becomes necessary.

*Why:* the volume is low and the real problem with vaccines is expiry and the cold chain,
not the balance. Solving the easy problem badly now makes solving the hard one well later
harder.

## Consequences

- Lifecycle events are immutable: the viewsets expose list/retrieve/create, deliberately
  without update or destroy.
- A dead or sold animal rejects later weighings and health events. Late entry with a
  retroactive date **is** accepted while the target is still active.
- The consumption of a dead animal stays charged. If the business decides otherwise, it
  enters through a manual counter-entry.
