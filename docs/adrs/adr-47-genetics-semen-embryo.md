---
title: adr-47-genetics-semen-embryo
type: adr
category: backend
use_case: load a bull or its EBVs, move straws or embryos, register a flush, sell semen, read genetic stock
created: 2026-07-28
modified: 2026-08-04
tags: [adr, feedlot, genetics, semen, embryo, inventory, event-sourced]
---

# ADR-47 — Genetics: semen, EBVs, and embryo transfer (`genetics`)

## CONTEXT

> Genetics as a first-class asset: own and external bulls, straws in the tank, their EBVs, and embryo transfer. Inventory is tracked by movements and the only economic fact the app produces is semen sales.

## ASSERTIONS

1. `genetics` separates editable catalogs — `Sire`, `SemenBatch`, `EmbryoBatch`, `BreedingValue`, with full CRUD — from immutable dated facts — `SemenMovement`, `EmbryoMovement`, `EmbryoFlush` and `SemenSale`, with `list`/`retrieve`/`create` and no `update` or `destroy` ([[adr-24-feedlot-domain]] rule 3).
2. The stock of a `SemenBatch` is derived from its movements and that of an `EmbryoBatch` from its own — Σ ins − Σ outs — exactly like `FeedStockMovement` ([[adr-25-account-ledger]] rule 4) and `InputStockMovement` ([[adr-37-inventory-and-weather]] rule 1). An editable `straws_remaining` is never stored.
3. A `Sire` optionally references an own `Animal` (`category=bull`) or represents an external bull whose semen is purchased without owning the animal. A `BreedingValue` is an EBV per bull — `trait`, `value`, `accuracy`, `source`, `date` — and is catalog data that is loaded, not a metric derived from system events: it is published by the genetic evaluation, not by own weighings.
4. `SemenSale` posts a `credit` `concept=sale` to the own account for the proceeds, via `(source_kind="semen_sale", source_id=<SemenSale.id>)` ([[adr-24-feedlot-domain]] rule 4), and deducts a `SemenMovement` `out` with `reason=sale`. Snapshots `unit_price × straws` as of the day ([[adr-25-account-ledger]] rule 3), same precedent as the own-livestock sale ([[adr-43-sale-settlement]] rule 3). The buyer is informational.
5. `EmbryoFlush` records the flush on a donor with its bull and grade, and produces inventory: creates or updates an `EmbryoBatch` and posts an `EmbryoMovement` `in`. Transfer to a recipient does not live here: it is a `Service` with `method=embryo_transfer` in `breeding` ([[adr-46-breeding-reproduction]] rule 7) that deducts the `out`.
6. No movement or flush posts an entry: own production and consumption are not delivered inputs. The `unit_cost` of a straw purchase is informational and generates no charge; the only entry in the app is the sale credit.
7. `register_semen_movement` rejects an inactive batch and a non-positive `quantity`; `register_semen_sale` rejects insufficient stock and a non-positive price, and builds the credit and the `out` in a transaction; embryo functions validate the same. A stock that goes negative due to partial loading is shown as an inconsistency, not blocked ([[adr-29-metrics-derivation]] rule 5).
8. `apps.metrics` derives straw stock by batch and by bull, total available semen, and usage by bull in the period. Without movements they return `null` with their `not_calculable`, never a filler zero.
9. `method`, `reason`, `trait`, `grade`, `direction` and other enums are English ([[LOCALIZATION]]); Spanish labels exist only in the render.

## FORBIDDEN

- **NEVER** store an editable straw or embryo counter (rule 2). It loses the history of why a tank's stock changed.
- **NEVER** post an entry for a movement or a flush (rule 6). Own consumption is already valued by the stock; the only economic fact is the sale.
- **NEVER** calculate an EBV from own weighings (rule 3). It is published by the genetic evaluation; deriving it here would invent a number no one endorses.
- **NEVER** record embryo transfer in `genetics` (rule 5). It is a reproductive event on an animal and belongs to `breeding`.
- **NEVER** sell more straws than are available (rule 7). The credit and the `out` are built together, in a transaction.

## REJECTED

- **Also charging the semen-buying client** — a debit in their account alongside the own credit. Out of scope: it enters through the same seam with its own change, not in this cut.
- **Billing semen consumed in an own AI** — treating the straw as a delivered input. Rejected by rule 6: it is an already-valued internal cost; the insemination charge to the boarding client is decided by `breeding` ([[adr-46-breeding-reproduction]] rule 6).
- **A genetics field on `Animal`** — the bull and its values hung on the animal. Rejected by the precedent of [[adr-32-multi-rubro-assets]] rule 2: `Sire.animal` references the existing `Animal` without adding anything to it.

## RELATED

### related adrs

- [[docs/adrs/adr-46-breeding-reproduction]] — the consumer: the service that deducts semen or embryo
- [[docs/adrs/adr-25-account-ledger]] — rules 3 and 4, the day price and stock by movements
- [[docs/adrs/adr-37-inventory-and-weather]] — rule 1, the generalized stock pattern
- [[docs/adrs/adr-43-sale-settlement]] — rule 3, the precedent of the `sale` credit in the own account
- [[docs/adrs/adr-29-metrics-derivation]] — the honest gap and the inconsistency that is shown

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `Sire`, `BreedingValue`, `SemenBatch`, `EmbryoBatch` and their movements
- [[docs/GLOSSARY-feedlot-additions]] — the genetics names, before first use
- [[docs/API]] — the `genetics` routes
