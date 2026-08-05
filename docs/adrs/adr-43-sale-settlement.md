---
title: adr-43-sale-settlement
type: adr
category: backend
use_case: register a sale exit, settle the fattening commission or own-account proceeds, read the own-account margin
created: 2026-07-26
modified: 2026-08-04
tags: [adr, feedlot, ledger, livestock, sale, settlement, phase-4c]
---

# ADR-43 — Sale settlement: fattening commission and own-account sale

## CONTEXT

> A sale exit leaves an economic record, and there are two distinct cases depending on who owns the livestock: the boarding client pays a commission for fattening, while own livestock produces feedlot income. The distinction is decided by `Client.kind`, and no settlement mutates an existing ledger entry.

## ASSERTIONS

1. Settling a sale posts a new `LedgerEntry` to the livestock owner's account. It edits or reopens nothing: feed and sanitary charges remain collected and the exit is not rewritten ([[adr-25-account-ledger]] rule 1). The entry is linked to the exit by `(source_kind="exit", source_id=<Exit.id>)` ([[adr-24-feedlot-domain]] rule 4).
2. Client livestock (`Client.kind=boarding`): the sale exit posts a **debit** `concept=service` for the fattening commission, `(engorde_commission_pct / 100) × kilos_ganados × sale_price_per_kg`. Weight gained is measured weigh-in to weigh-out across measurable intervals ([[adr-29-metrics-derivation]] rule 3). The entry snapshots `unit_price` and `quantity` as of the day ([[adr-25-account-ledger]] rule 3).
3. Own livestock (`Client.kind=own`): the sale exit posts a **credit** `concept=sale` for `weight × sale_price_per_kg` to the own account. Since that account already accumulates costs as debits, the credit offsets them and the net balance tends toward the margin.
4. Settlement is gated by its inputs and posts nothing when `sale_price_per_kg` is missing; when in the boarding case `engorde_commission_pct` is missing or weight gained is not measurable, they yield zero or negative; or when in the own case `weight` is missing. The exit is recorded regardless, without settlement.
5. Settlement applies exclusively to `Exit.kind=sale`. A death still does not touch the ledger, and a `transfer` or `other` exit also posts nothing: there was no sale to settle, and already-charged consumption is not reversed.
6. Which entry is posted is decided by the owner's `Client.kind`, resolved from the `Animal` or `Lot` of the exit. The only new field is `engorde_commission_pct` (nullable), which applies only to the boarding case; there is no "settlement mode" that duplicates `kind`.
7. There is no `Settlement` table: settlement is a `LedgerEntry`. `register_exit` gains the gated logic and already-loaded exits remain valid — settlement applies going forward and does not reprocess the past.

## FORBIDDEN

- **NEVER** mutate an entry to settle (rule 1). A settlement is a new fact, not a correction of the past.
- **NEVER** post a charge when an input is missing (rule 4). A fabricated entry is worse than a fabricated metric: it moves a real client balance.
- **NEVER** charge the commission on total weight (rule 2). That would include the intake weight the client already had; what the feedlot charges is the fattening.
- **NEVER** settle a death or a non-sale exit (rule 5). There was no sale, and reversing consumption for an exit would be a separate commercial, not technical, decision.
- **NEVER** add a field that duplicates the `Client.kind` distinction (rule 6). Two fields saying the same thing will eventually contradict each other.

## REJECTED

- **A separate `Settlement` model** — settlement as its own table with its own state. Rejected by rule 7: settlement *is* an entry, and a parallel table would be a second place to look for what was charged.
- **Recording the boarding client's sale price as own income** — taking the full boarding sale. Rejected: the sale belongs to the client and the feedlot charges for the fattening service, not the proceeds.
- **Re-settling already-loaded exits** — walking the past and applying the new rule. Not done (rule 7); if needed it is an explicit action with its own change.
- **`Exit` with no economic record** — the prior policy, where `sale_price_per_kg` was informational and no exit posted. Replaced by this ADR, which [[adr-25-account-ledger]] rule 6 required as its vehicle.

## RELATED

### related adrs

- [[docs/adrs/adr-25-account-ledger]] — rules 1, 3 and 6, the immutable entry, the day price, and the deferral this fulfills
- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — the exit and death, and what part remained intact
- [[docs/adrs/adr-24-feedlot-domain]] — rule 4, the generic pair that links the entry to the exit
- [[docs/adrs/adr-29-metrics-derivation]] — rules 2 and 3, weight gained and the honest gap
- [[docs/adrs/adr-47-genetics-semen-embryo]] — the same `Concept.SALE` in semen sales

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `Exit`, `LedgerEntry`, `Client`
- [[docs/feedlot/15-liquidacion-de-venta-propuesta]] — the commercial model the owner defined
- [[docs/API]] — the exits route
