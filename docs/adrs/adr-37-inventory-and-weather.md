---
title: adr-37-inventory-and-weather
type: adr
category: backend
use_case: load a non-feed input, record a stock entry or exit, log rainfall or weather, read current stock
created: 2026-07-25
modified: 2026-08-04
tags: [adr, feedlot, inventory, weather, stock, phase-10]
---

# ADR-37 — General input inventory and weather log

## CONTEXT

> Two missing facts: how much input there is —diesel, posts, wire, field supplies— and how much it rained. Stock is generalized from the feed movement pattern; neither touches the ledger.

## ASSERTIONS

1. `InputStockMovement` records dated inflows and outflows of an `InputType` by `(owner_kind, client)`, and current stock is derived —Σ entries − Σ exits— exactly as `FeedStockMovement` does ([[adr-25-account-ledger]] rule 4). An editable `stock` field is never stored on `InputType`.
2. `InputType` is an editable catalog with full CRUD: "loading inputs" means creating types. `InputStockMovement` is a dated fact: `list`/`retrieve`/`create`, no `update` or `destroy` ([[adr-24-feedlot-domain]] rule 3), and a correction is another movement.
3. No `InputStockMovement` posts a ledger entry. An input purchased for the feedlot is own consumption, not an input delivered to a client ([[adr-32-multi-rubro-assets]] rule 4). The `unit_price` of an entry is informational —it values the stock— and does not generate a charge.
4. `register_input_movement` rejects at the service layer —not at the view— an `InputType` with `is_active=False` and a non-positive `quantity`. Late-entry with a backdated date is accepted, and a stock that goes negative due to partial loading is shown as an inconsistency rather than being blocked ([[adr-29-metrics-derivation]] rule 5).
5. `WeatherLog` records per date and `site` the rainfall (`rainfall_mm`) and, optionally, minimum and maximum temperature and a note. Idempotent by `(site, date)`: re-registering updates the row, it does not duplicate. It posts no ledger entry and references no livestock or account: it is environmental context that the metrics read.
6. `apps.metrics` gains two pure reads —current stock by input and rainfall summary for the period— without defining any new business number ([[adr-29-metrics-derivation]] rule 1). `Animal`, `Lot`, and `feed` are not refactored: the extraction looks forward ([[adr-32-multi-rubro-assets]] rule 2).

## FORBIDDEN

- **NEVER** store an editable stock field on `InputType` (rule 1). A manually written balance loses the history of why it changed.
- **NEVER** post a ledger entry for an input movement (rule 3). It is own consumption, and the only charging path remains the ledger via `feed`.
- **NEVER** block an entry because stock would go negative (rule 4). The operator would falsify the date, and that is where the data is truly lost.
- **NEVER** validate the input in the view (rule 4). The rule lives in the service, shared by view, admin, and command.
- **NEVER** couple `WeatherLog` to livestock or an account (rule 5). Rainfall is context for decisions, not a transaction.

## REJECTED

- **Copying `FeedStockMovement` per input** — a stock model per type of thing. It is the duplication that triggers the extraction: a single generic movement covers all and leaves only one to maintain.
- **Migrating feed to the generic stock** — unifying `FeedStockMovement` inside `inventory`. Rejected by the same criterion as [[adr-32-multi-rubro-assets]] rule 2: rewriting what works for symmetry alone is risk with no return.
- **Charging the client for the input from here** — invoicing diesel or wire as a service. Out of scope: if it is ever invoiced, it enters through the generic pair `(source_kind, source_id)` with its own change.

## RELATED

### related adrs

- [[docs/adrs/adr-25-account-ledger]] — rule 4, the stock-by-movements pattern this generalizes
- [[docs/adrs/adr-32-multi-rubro-assets]] — rules 2 and 4, forward extraction and own consumption
- [[docs/adrs/adr-29-metrics-derivation]] — rules 1 and 5, derive and surface the inconsistency
- [[docs/adrs/adr-47-genetics-semen-embryo]] — the same pattern applied to straws and embryos

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `InputType`, `InputStockMovement`, `WeatherLog`
- [[docs/API]] — the inventory and weather routes
