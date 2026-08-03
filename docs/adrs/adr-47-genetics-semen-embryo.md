---
title: adr-47-genetics-semen-embryo
type: adr
status: active
created: 2026-07-28
tags: [adr, feedlot, genetics, semen, embryo, inventory, event-sourced, phase-breeding]
---

# ADR-47 — genetics: semen, EPDs and embryo transfer (`genetics`)

**Context:** grows by addition on top of the spine
([[adr-49-domain-layer-and-growth-by-addition]] rule 1): a new `genetics` app, without touching
`livestock`. Reuses the stock-by-movements pattern of [[adr-25-account-ledger]] rule 4
(`FeedStockMovement`) generalized by [[adr-37-inventory-and-weather]] rule 1; the "an own sale is
a `concept=sale` credit in the own account" precedent of [[adr-43-sale-settlement]] decision 3;
and the "own production/consumption does not touch the ledger" criterion of
[[adr-32-multi-rubro-assets]] rule 4 and [[adr-37-inventory-and-weather]] rule 3. It is consumed
by [[adr-46-breeding-reproduction]] (the `Service` draws down a straw or an embryo). Rules only;
the entities live in [[FEEDLOT-DATA-MODEL]], the names in [[GLOSSARY]]
(`GLOSSARY-feedlot-additions.md`) before their first use ([[adr-01-glossary-and-localization]]).

## Context

A cow-calf herd manages **genetics** as a first-class asset: bulls (sires), own or external,
semen straws kept in tanks, their EPDs (expected progeny differences), and embryo transfer with
donors and recipients. Today the system does not know what semen there is, from which bull, how
many straws are left, nor does it record a semen sale — which the owner defined as **own
revenue**. The `genetics` app is added with the genetic catalog, the straw and embryo inventory
by movements, and the semen sale, without touching the stable domain.

## Decisions

### 1. `genetics` separates editable catalogs from immutable movements

Catalogs (master data, ModelViewSet with full CRUD): `Sire`, `SemenBatch` (a batch of straws),
`EmbryoBatch` and `BreedingValue` (an EPD). Immutable dated facts (`list`/`retrieve`/`create`,
without `update` or `destroy`, [[adr-49-domain-layer-and-growth-by-addition]] rule 3):
`SemenMovement`, `EmbryoMovement`, `EmbryoFlush` (collection) and `SemenSale`.

*Why:* a bull or a batch has state that gets corrected (it is retired, it is renamed); a stock
movement or yesterday's sale is not rewritten. The same catalog/event boundary as the rest of the
system ([[adr-37-inventory-and-weather]] rule 2).

### 2. Straw and embryo stock is Σ ins − Σ outs, never an editable field

A `SemenBatch`'s stock is **derived** from its `SemenMovement`s (`in`/`out`), and an
`EmbryoBatch`'s from its `EmbryoMovement`s — exactly like `FeedStockMovement`
([[adr-25-account-ledger]] rule 4) and `InputStockMovement` ([[adr-37-inventory-and-weather]]
rule 1). An editable `straws_remaining` field is never stored on the batch.

*Why:* the same discipline as the whole system. An editable balance loses the history of why it
changed; the movement preserves it and makes a tank's stock auditable.

### 3. A `Sire` links to an own `Animal` or is external; EPDs are catalog, not derived

`Sire` optionally references an own `Animal` (`category=bull`) or represents an **external** bull
whose semen is bought without owning the animal (`registry_id`, `breed`). It is an editable
catalog. A `BreedingValue` is an EPD per bull: `(trait, value, accuracy, source, date)` — `trait`
∈ {`birth_weight`, `weaning_weight`, `milk`, `ribeye_area`, `marbling`, `scrotal`, `other`} —; it
is catalog data that is loaded, not a metric derived from the system's events.

*Why:* EPDs are published by the genetic evaluation (the stud, the breed association, an external
service), they are not computed from one's own weighings; modelling them as an editable catalog is
the correct call. An external `Sire` covers the real case of buying semen from a bull that is not
yours.

### 4. The semen sale is own revenue: a `sale` credit to the own account

`SemenSale` posts **one `credit` with `concept=sale`** to the own account (the
`Client(kind=own)`) for the sale proceeds, via the generic pair `(source_kind="semen_sale",
source_id=<SemenSale.id>)` ([[adr-49-domain-layer-and-growth-by-addition]] rule 4), and draws down
a `SemenMovement` `out` (`reason=sale`) from the `SemenBatch`. It is the same precedent as the
sale of own cattle ([[adr-43-sale-settlement]] decision 3): own proceeds are recorded as a credit
in the account that carries their costs, leaving the margin legible. It snapshots the day's
`unit_price` × `straws` ([[adr-25-account-ledger]] rule 3). The buyer is informative
(`buyer_name`, optional `buyer_client`).

*Why:* the owner defined the semen sale as feedlot revenue. Recording it as a credit in the own
account — just like the sale of own cattle — makes it comparable against the genetic costs
without inventing a separate income statement the ledger does not model. Additionally charging a
buying client is a future addition through the same seam, not part of this cut.

### 5. Embryo transfer: the flush produces inventory; the transfer consumes it in `breeding`

`EmbryoFlush` (a collection on a donor `Animal`) records the embryos obtained with their donor,
their bull and their grade, and produces inventory: it creates/updates an `EmbryoBatch` and posts
an `EmbryoMovement` `in`. The **transfer** to a recipient does **not** live here: it is a
`Service` with `method=embryo_transfer` in `breeding` ([[adr-46-breeding-reproduction]] decision
7) that draws down an `EmbryoMovement` `out`. `genetics` keeps the inventory; `breeding` the
reproductive event on the recipient.

*Why:* the flush is an inventory-production fact (like a purchase of straws); the transfer is a
reproductive fact on an animal, which belongs with `breeding`'s events alongside the service and
the calving. Each fact lives in its own domain and the inventory is not duplicated.

### 6. Neither the inventory nor the flush touches the ledger; only the sale posts

No `SemenMovement`, `EmbryoMovement` or `EmbryoFlush` posts an entry — own production and
consumption are not inputs delivered to a client ([[adr-32-multi-rubro-assets]] rule 4,
[[adr-37-inventory-and-weather]] rule 3). A straw purchase's `unit_cost` is **informative** (it
values the stock) and generates no charge. The app's only entry is the sale credit (decision 4).
Consumption by insemination is a stock `out`, with no entry; its eventual invoicing to the
boarding client is decided by `breeding` as a service debit
([[adr-46-breeding-reproduction]] decision 6), not by `genetics`.

*Why:* a single charging path. Semen consumed in one's own AI is an internal cost already valued
by the stock; sold semen is the only economic fact that comes out of `genetics`.

### 7. Every movement and sale validates in the service, not in the view

`register_semen_movement` rejects an inactive `SemenBatch` and a non-positive `quantity`;
`register_semen_sale` rejects insufficient stock and a non-positive price, and assembles the
credit and the `out` in one transaction; `register_embryo_flush` and `register_embryo_movement`
validate the same way over embryos. A stock left negative by partial loading is **shown** as an
inconsistency, not blocked ([[adr-37-inventory-and-weather]] rule 4,
[[adr-29-metrics-derivation]] rule 5). Late entry with a retroactive date is accepted.

*Why:* business rules live in the service, the single write point, so that view, admin and command
share the same validation.

### 8. Genetics metrics are derived in `apps.metrics`, honest about the gap

`apps.metrics` gains pure functions over the movements ([[adr-29-metrics-derivation]] rule 1):
straw stock per batch and per bull, total available semen, and usage per bull in the period. With
no movements, they return `null` with their `not_calculable`, never a filler zero
([[adr-29-metrics-derivation]] rule 2).

*Why:* "0 straws" and "semen from this bull was never loaded" are opposite situations; the
explicit gap distinguishes them.

### 9. `choices` in English; Spanish lives only in the render

`method`, `reason`, `trait`, `grade`, `direction` and the other enums are English
([[adr-01-glossary-and-localization]], [[LOCALIZATION]]); the Spanish labels exist only in the
frontend's rendered output.

## Consequences

- The backend enters only through [[API]] ([[adr-03-api-and-backend]]) and is born through the
  [[TDD]] flow ([[adr-07-development-flow]]); this ADR grants no exception to that path
  ([[adr-49-domain-layer-and-growth-by-addition]] rule 6).
- Migrations: the new tables live in `genetics` (`Sire`, `BreedingValue`, `SemenBatch`,
  `SemenMovement`, `SemenSale`, `EmbryoBatch`, `EmbryoMovement`, `EmbryoFlush`). Nothing outside
  the app; the sale credit reuses `Concept.SALE` ([[adr-43-sale-settlement]]) through the seam,
  with no new concept and no new model in `ledger`.
- `Sire.animal` references the existing `Animal` without adding a field to it — the extraction
  looks forward ([[adr-32-multi-rubro-assets]] rule 2, [[adr-38-senasa-traceability]]'s ear tag
  precedent).
- No environment variables are added: `genetics` is internal data, with no credentials and no
  external services.
- The RBAC gating of these routes is declared in [[API]] with its permission class before the code
  ([[adr-44-field-operational-roles]] decision 7).
- Any change to rules 1–9 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
