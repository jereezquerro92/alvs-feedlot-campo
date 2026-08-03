---
title: adr-32-multi-rubro-assets
type: adr
status: active
created: 2026-07-24
tags: [adr, feedlot, multi-rubro, assets, crops, machinery, phase-6]
---

# ADR-32 — multiple business lines: extracting `assets` and the `crops` and `machinery` lines

**Context:** the first real second business line; it triggers the extraction foreseen in
[[14-preparacion-fase6]]. Extends [[adr-49-domain-layer-and-growth-by-addition]] ("grows by addition"),
reuses the ledger of [[adr-25-account-ledger]] without touching it, and takes the XOR constraint of
[[adr-26-livestock-individual-and-lot]] as a precedent of shape.

## Context

Up to Phase 5 the system knew a single business line: cattle. The feedlot also produces its
own alfalfa on irrigation pivots (circles), cuts it several times a season, and maintains
machinery with its services. Recording circles, cuttings, tasks, machines and maintenance is
what this phase asks for.

Building crops and machinery by copying `Animal`/`Lot` and their events would have
duplicated three near-identical models — the alarm signal [[14-preparacion-fase6]] sets for
extracting the shared abstractions. Two new business lines at once is exactly the trigger:
what is common is pulled into an `assets` app, and only then, not before (YAGNI: it was not
extracted in Phase 1 with a single line).

## Decisions

### 1. `assets` supplies abstractions, not tables

`assets` has no concrete models and no table migrations of its own: it exposes two abstract
bases — `AssetBase` (an asset's identity + lifecycle) and `CostedEvent` (an event that
snapshots `unit_price`×`quantity` and posts a `service` debit). `crops` and `machinery`
inherit from them.

*Why:* it is the same idiom `LifecycleEvent` already uses in `livestock` (adr-28 rule 1):
share the shape without merging domains. A concrete asset lives in its own line's app and
keeps its own table; what is common is not paid for twice.

### 2. `Animal`/`Lot` are NOT refactored backwards

The existing cattle domain is not rewritten to inherit from `AssetBase`. The extraction
looks forward: it covers the new lines, it does not migrate the one that already works.

*Why:* rewriting models with data, migrations and passing tests purely for symmetry is risk
with no return. The precedent of shape (adr-26) is enough; literal inheritance adds nothing
that would justify touching the stable domain.

### 3. Costing enters through the generic pair, without changing `ledger`

`FieldTask` and `MaintenanceEvent` post a `debit` with the **already existing**
`Concept.SERVICE`, via `post_entry(...)` with
`source_kind ∈ {"field_task","maintenance_event"}` and the event's `source_id` — the
`(source_kind, source_id)` pair of [[adr-49-domain-layer-and-growth-by-addition]] rule 4. `ledger` gains
no model, no concept and no per-line FK.

*Why:* it is the scalability seam doctrine reserved for exactly this. A new line that
charges does not touch `ledger`; the seam has been in place since Phase 1.

### 4. The cutting does not touch the ledger; the task and the maintenance do

`Cutting` is an immutable production event: it records harvested kilos, it posts no entry.
`FieldTask` and `MaintenanceEvent` are costs: they always post.

*Why:* a cutting is not an input delivered to a client, it is one's own harvest — there is
nobody to charge. The ledger charges inputs delivered (adr-25 rule 6, the same criterion
that leaves `Weighing`/`Death` without an entry). Bridging a cutting into own feed stock
(`FeedStockMovement`) is an explicit future addition, not part of this phase: it is added
when the business asks for it, with its own change.

### 5. Every task and every maintenance charges a client

`FieldTask` and `MaintenanceEvent` carry a mandatory `client` and always post. The feedlot
itself is a `Client(kind=own)`; its internal costs accumulate in that account, exactly as
its own cattle already does.

*Why:* modelling a "no client / no charge" origin that is not used today is speculative
complexity (the same criterion as adr-28 rule 5 for health). If tomorrow a task is done as
a service for a third party, `client` already covers it without changing the model.

### 6. Assets are editable catalogs; events are immutable

`Pivot`, `Machine` and `Crop` are master data: a ModelViewSet with full CRUD ("recording
circles" is creating pivots). `Cutting`, `FieldTask` and `MaintenanceEvent` are operational
events: list/retrieve/create, without update or destroy (adr-49 rule 3).

*Why:* an asset has state that gets corrected (a pivot is retired, a machine is renamed);
an operational event is a dated fact that is only corrected with another event, never by
editing the past.

### 7. Categories, statuses and species are `choices` in English

`species`, `category`, `kind`, `status` are English enums ([[LOCALIZATION]]); Spanish lives
only in the frontend's render.

## Consequences

- The existing cost metrics (`cost_breakdown` sums debits by `concept`) already pick up
  tasks and maintenance as `service` without touching `apps.metrics`: the new line composes,
  it does not reform.
- A retired pivot or machine (`status=retired`) rejects new events in the service, not in
  the view — the same posture as a dead animal (adr-28).
- `assets` remains the home of the next shared abstraction (horses or another line enter by
  inheriting, not by copying). The extraction was done once and for all.
- Any change to rules 1–5 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
