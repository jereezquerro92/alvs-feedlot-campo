---
title: adr-32-multi-rubro-assets
type: adr
category: backend
use_case: add a new category, load pivots, cuttings, machines, or maintenance events, inherit from asset bases, cost an event that is not livestock
created: 2026-07-24
modified: 2026-08-04
tags: [adr, feedlot, multi-rubro, assets, crops, machinery]
---

# ADR-32 — Multi-category: the `assets` extraction and the `crops` and `machinery` categories

## CONTEXT

> The first real second category: alfalfa on pivots and machinery with its maintenance. Two categories at once are the trigger to extract what is common into `assets`, and that is the moment — not before, with a single category, and not backward onto livestock that already works.

## ASSERTIONS

1. `assets` provides abstractions and not tables: it exposes `AssetBase` (identity and lifecycle of an asset) and `CostedEvent` (an event that captures `unit_price × quantity` and posts a `service` debit). `crops` and `machinery` inherit from them and each concrete asset keeps its own table, the same idiom as `LifecycleEvent` in `livestock` ([[adr-28-animal-lifecycle-and-sanitary]] rule 1).
2. `Animal` and `Lot` are not refactored backward. The extraction looks forward: it covers the new categories, not the one that already works with data, migrations, and passing tests.
3. Costing enters through the generic pair: `FieldTask` and `MaintenanceEvent` post a `debit` with the existing `Concept.SERVICE`, via `post_entry` with `source_kind ∈ {"field_task", "maintenance_event"}` ([[adr-24-feedlot-domain]] rule 4). `ledger` gains no model, concept, or FK per category.
4. `Cutting` is an immutable production event — it records harvested kilos and posts no ledger entry, because own-farm harvest is not an input delivered to a client —. `FieldTask` and `MaintenanceEvent` are costs and always post.
5. Every task and every maintenance event carries a mandatory `client`. The feedlot itself is a `Client(kind=own)` and its internal costs accumulate in that account, the same as its own livestock.
6. `Pivot`, `Machine`, and `Crop` are editable catalogs with full CRUD; `Cutting`, `FieldTask`, and `MaintenanceEvent` are events: `list`/`retrieve`/`create`, without `update` or `destroy` ([[adr-24-feedlot-domain]] rule 3). A `retired` pivot or machine rejects new events in the service, not in the view.
7. `species`, `category`, `kind`, and `status` are enums in English ([[LOCALIZATION]]); Spanish lives only in the render.

## FORBIDDEN

- **NEVER** copy `Animal`/`Lot` and its events for a new category (rule 1). Three near-identical models are the signal that triggers the extraction, not a way to proceed.
- **NEVER** rewrite livestock to inherit from `AssetBase` (rule 2). That is risk without return on a stable domain, done only for symmetry.
- **NEVER** add to `ledger` a model, concept, or FK for a new category (rule 3). The generic seam exists precisely so that a billing category need not touch it.
- **NEVER** post a ledger entry for a cutting (rule 4). It is own-farm harvest: there is no one to charge.
- **NEVER** validate asset state in the view (rule 6). The business rule lives in the service, the single write point shared by the view, admin, and command.

## REJECTED

- **Extracting `assets` in Phase 1** — shared abstractions from the start, with a single category. Not done due to YAGNI: with one category there is nothing common to share, and the abstraction would have been a conjecture about the second.
- **A "no client / no charge" origin for tasks and maintenance events** — an event that charges no one. Rejected as speculative complexity (same criterion as [[adr-28-animal-lifecycle-and-sanitary]] on sanitary care): `Client(kind=own)` already absorbs internal costs.
- **Bridging the cutting to own feed stock** — a `Cutting` producing an `in` for `FeedStockMovement`. Explicitly deferred: it enters when the business asks for it, with its own change, not as a side effect of this phase.

## RELATED

### related adrs

- [[docs/adrs/adr-24-feedlot-domain]] — rules 3 and 4, growth by addition and the costing seam
- [[docs/adrs/adr-25-account-ledger]] — what the ledger charges and what it does not
- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — the abstract idiom and the anti-speculative criterion
- [[docs/adrs/adr-37-inventory-and-weather]] — the same extraction, applied to input stock

### related files

- [[docs/feedlot/14-preparacion-fase6]] — the alarm signal that triggers the extraction
- [[docs/FEEDLOT-DATA-MODEL]] — `Pivot`, `Machine`, `Crop`, `Cutting`, `FieldTask`, `MaintenanceEvent`
- [[docs/constitution/LOCALIZATION]] — English in code, Spanish in the render
