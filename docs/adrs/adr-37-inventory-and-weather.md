---
title: adr-37-inventory-and-weather
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, inventory, weather, stock, phase-10]
---

# ADR-37 — general input inventory and weather logging

**Context:** generalizes the stock pattern of [[adr-25-account-ledger]] rule 4
(`FeedStockMovement`) to inputs that are not feed (diesel, posts, wire, field sanitary
products) and adds rainfall/weather logging. Reuses the event-sourced posture of
[[adr-49-domain-layer-and-growth-by-addition]] rule 3 and the "own production/consumption does
not touch the ledger" precedent of [[adr-32-multi-rubro-assets]] rule 4. Rules only; the
entities live in [[FEEDLOT-DATA-MODEL]].

## Context

The feedlot moves inputs that are not feed — diesel for the machinery, posts and wire for the
pens, field sanitary products — and today it has nowhere to record them. And it sustains
decisions (sowing, grazing, sanitary work) on rainfall, which is not recorded either. Two
facts are missing: **how much input there is** and **how much it rained**.

Copying `FeedStockMovement` per input would have duplicated the same model — the signal to
extract the abstraction. An `inventory` app is added with generic stock by movements, and a
`weather` app with the weather log. Neither touches the existing feed nor the ledger.

## Decisions

### 1. Input stock is the sum of movements, never an editable number

`InputStockMovement` records dated ins and outs of an `InputType` per `(owner_kind, client)`.
Current stock is **derived** — Σ ins − Σ outs — exactly like `FeedStockMovement` (adr-25 rule
4). An editable `stock` field is never stored on `InputType`.

*Why:* the same discipline as the whole system. An editable balance loses the history of why
it changed; the movement preserves it and makes the stock auditable.

### 2. `InputType` is an editable catalog; the movement is immutable

`InputType` (diesel, posts, wire, sanitary product…) is master data: a ModelViewSet with full
CRUD — "loading inputs" is creating types. `InputStockMovement` is a dated fact:
list/retrieve/create, without update or destroy (adr-49 rule 3). A correction is another
movement.

*Why:* an input type has state that gets corrected (it is retired, it is renamed);
yesterday's movement is not rewritten.

### 3. Inventory does NOT touch the ledger

No `InputStockMovement` posts an entry. An input bought for the feedlot is own consumption,
not an input delivered to a client that gets charged (the same criterion as `Cutting`/adr-32
rule 4 and one's own harvest). An entry's `unit_price` is **informative** — it allows valuing
the stock — and generates no charge.

*Why:* a single charging path remains the ledger via `feed` (adr-25). If one day an input is
invoiced as a service to a third party, it enters through the generic `(source_kind,
source_id)` pair (adr-49 rule 4) with its own change, not through here.

### 4. An inactive `InputType` rejects new movements, in the service

`register_input_movement` rejects, in the **service** (not in the view), an `InputType` with
`is_active=False` and a non-positive `quantity`. Late entry with a retroactive date is
accepted. A stock left negative by partial loading is **not blocked**: it is shown as an
inconsistency (the posture of adr-29 rule 5 — show, do not block), rather than falsifying the
date in order to be able to load.

*Why:* business rules live in the service, the single write point, so that view, admin and
command share the same validation.

### 5. Weather is an immutable event, independent of the ledger and of the domain

`WeatherLog` records per date the rainfall (`rainfall_mm`) and, optionally, min/max
temperature and a note, per `site`. It is an immutable dated fact: list/retrieve/create. It
posts no entry, references neither cattle nor account — it is environmental data the metrics
read, not an economic fact.

*Why:* rainfall is context for deciding, not a transaction. Modelling it as an immutable
event keeps it auditable and aggregatable without coupling it to any domain.

## Consequences

- The backend enters only through [[API]] (adr-03) and is born through the [[TDD]] flow
  (adr-07).
- `apps.metrics` gains two pure reads: current stock per input and the period's rainfall
  summary. It defines no new business number, it only aggregates over the new events (adr-29
  rule 1).
- No environment variables are added: both apps are internal data, with no credentials and no
  external services.
- `Animal`/`Lot` and `feed` are not refactored: the extraction looks forward, it covers the
  new inputs, it does not migrate the feed that already works (the same criterion as adr-32
  rule 2).
- Any change to rules 1–5 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
