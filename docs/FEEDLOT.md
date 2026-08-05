---
title: FEEDLOT
type: reference
category: project
use_case: understanding what the feedlot does and which app owns which fact
created: 2026-07-21
modified: 2026-08-04
tags: [doc, feedlot, domain, ssot]
---

# FEEDLOT — the farm-traceability domain

> [!note] Scope of this doc
> The code-facing SSOT of the **domain**: which apps exist and what each owns
> ([[adr-24-feedlot-domain]] rule 5). Entities and their relations are
> [[FEEDLOT-DATA-MODEL]]; endpoints are `API-feedlot-additions.md` → [[API]]; the
> objective is [[PRD]]. Force for every rule summarized here lives in the ADRs
> this file links — never here.

## The objective

Traceability for a feedlot that runs **own cattle** and **boarding** (custom feeding
of third parties' cattle, billed for feed and services). Every input applied to an
animal is recorded, attributed to its owner, and cross-referenced against its outcome
(gain, conversion, mortality, sale). Everything a feedlot input touches is billed to
the owner's current account in ARS at the price of the day. The same spine now carries
other farm domains — this is [[PRD]]'s "grows by addition", instantiated and shipped.

## Domain apps

Grouped as [[PRD]] groups them. Model names are indicative; [[FEEDLOT-DATA-MODEL]] owns
the entities and their relations.

### Spine — shared, reused by every domain

- `clients` — `Client`, `Account`: who is charged.
- `ledger` — `LedgerEntry`, `Payment`, `PaymentAllocation`: the immutable current account
  ([[adr-25-account-ledger]], [[adr-41-payment-allocation]]).
- `assets` — `AssetBase`, `CostedEvent`: the shared asset and costed-event abstractions a
  new domain inherits instead of duplicating ([[adr-32-multi-rubro-assets]]).
- `market` — `MarketSource`, `MarketPrice`: reference prices and their connectors
  ([[adr-30-market-prices-connectors]]).
- `fx` — `FxRate`: currency ([[adr-39-gross-margin-and-fx]]).

### Cattle

- `livestock` — `Lot`, `Animal`, `Intake`, `LifecycleEvent`, `Weighing`, `Death`, `Exit`
  ([[adr-26-livestock-individual-and-lot]], [[adr-28-animal-lifecycle-and-sanitary]]).
- `feed` — `FeedType`, `FeedDelivery`, `FeedStockMovement`, `FeedingEvent`.
- `feedyard` — `Pen`, `Ration`, `RationLine`, `LoadingOrder`, `PenPlacement`, `BunkScore`:
  the daily operating loop ([[adr-33-feedyard-operating-loop]], [[adr-34-pen-placement]],
  [[adr-42-pen-conversion-honest-cut]]).
- `sanitary` — `HealthProduct`, `HealthEvent`, `SanitaryPlan`, `SanitaryPlanItem`,
  `PlanEnrollment`: animal health and the sanitary plan
  ([[adr-28-animal-lifecycle-and-sanitary]], [[adr-40-sanitary-plan-schedule]]).
  **Not `health`** — that name is the template's `/api/health/` liveness app, and the
  collision was resolved by renaming this one ([[adr-28-animal-lifecycle-and-sanitary]]
  rule 4).
- `traceability` — `Establishment`, `TransitDocument`, `Caravana`: regulatory identity and
  movement ([[adr-38-senasa-traceability]]).

### Herd

- `breeding` — `Service`, `PregnancyCheck`, `Calving`, `Weaning`, `IatfProtocol`:
  reproduction ([[adr-46-breeding-reproduction]]).
- `genetics` — `Sire`, `BreedingValue`, `SemenBatch`, `EmbryoBatch` and their movements
  and sales ([[adr-47-genetics-semen-embryo]]).

### Other domains

- `crops` — `Pivot`, `Crop`, `Cutting`, `FieldTask`: alfalfa on irrigation pivots
  ([[adr-32-multi-rubro-assets]]).
- `machinery` — `Machine`, `MaintenanceEvent`: the fleet and its maintenance
  ([[adr-32-multi-rubro-assets]]).

### Across all

- `metrics` — no models: every value is derived, never stored
  ([[adr-29-metrics-derivation]], [[adr-39-gross-margin-and-fx]]).
- `expenses` — `ExpenseEvent`: extra charges (labor/fuel/machinery) billed to a client
  through the ledger seam, never a manual debit ([[adr-44-field-operational-roles]]
  rule 6).
- `inventory` — `InputType`, `InputStockMovement`; `weather` — `WeatherLog`
  ([[adr-37-inventory-and-weather]]).
- `notifications` — `Notification`: the digest ([[adr-36-notifications-digest]]).
- `advisors` — `Advisor`, `AdvisorReport`: read-only generative analyses over a client's
  own metrics ([[adr-27-advisors-generative]], [[adr-31-advisors-implementation]]).
- `assistant` — `Conversation`, `Message`: the per-client conversational assistant,
  read-only forever ([[adr-35-conversational-assistant]]).

App naming follows [[GLOSSARY]] (lowercase, domain-named, singular PascalCase models).
New nouns are added to [[GLOSSARY]] first (`GLOSSARY-feedlot-additions.md`).

## Business rules (summary; force in the ADRs)

Only the rules that cut across the domain live here. Each domain's own depth is owned by
its ADR above.

### Intake — two modes ([[adr-26-livestock-individual-and-lot]])

Cattle enter either **individually** (one `Animal` per ear tag) or **as a lot**
(head count + total weight, no per-head identity). `Weighing`, `Death`, `Exit` target
an `Animal` **or** a `Lot`.

### Feed origin and costing ([[adr-25-account-ledger]])

A `FeedingEvent` records an `origin`:

- `client_stock` — decrements the client's feed stock; **no ledger charge** (the client
  already provided the feed). Still valued for consumption metrics.
- `own_stock` — decrements the feedlot's stock **and** posts a `debit` `LedgerEntry`
  (`quantity × unit_price` of the day).

Metrics value **all** consumption regardless of origin; billing charges **only**
`own_stock`. Separating billing from the consumption metric is the crux of the rule.

### Sanitary

`HealthEvent` (vaccine/treatment) always posts a `debit` — it is a feedlot input
([[adr-28-animal-lifecycle-and-sanitary]]). The plan and its schedule are
[[adr-40-sanitary-plan-schedule]].

### Current account ([[adr-25-account-ledger]])

An immutable ledger. Debits from feeding/sanitary/services, credits from `Payment` and
adjustments. Sign: positive balance = client owes. No edits, no deletes — corrections
are counter-entries. Every debit snapshots `unit_price` and `quantity` (historical price).

### The costing seam ([[adr-24-feedlot-domain]] rule 4)

A charge-bearing event reaches the account through the `(source_kind, source_id)` pair on
`LedgerEntry`, never through a per-domain foreign key. Every domain above posts its charges
through that one pair — which is why `crops` and `machinery` were added without changing
`ledger`. This is the sanctioned scalability seam; a new domain uses it too.

### Roles and the client portal ([[adr-44-field-operational-roles]], [[adr-45-lot-owner-assistant-access]])

Six operative field roles are Django Groups; the matrix of who reads/writes which area
lives in one file, `apps/users/roles.py` ([[adr-44-field-operational-roles]] rule 1).
`lot_owners` is a **client portal**: read-only and confined to the single `Client` bound
to its `AccessRequest`, reaching exactly three client-keyed surfaces — metrics, the account,
and the conversational assistant ([[adr-45-lot-owner-assistant-access]]). Reference market
prices (`market`) are staff-only cross-client data, shown in the redesign's *precios*
module and never scoped to a tenant. The users module is reference-only: a grant is an
admin action in `/admin/`, never self-service ([[adr-20-authorization-lobby]] rule 3).

## Localization

Domain nouns and choices are English in code ([[LOCALIZATION]]); Spanish exists only in
the frontend's rendered output through the i18n catalog. Default locale is `es`.

## Out of scope

Tax/AFIP invoicing, scale hardware integration, transport documents beyond the
`traceability` app's own ([[adr-38-senasa-traceability]]), and payroll. A domain absent
from this list is not out of scope — it is simply not built yet, and enters the same way
every shipped domain did ([[adr-07-development-flow]]).
