---
title: adr-25-account-ledger
type: adr
status: proposed
created: 2026-07-21
tags: [adr, feedlot, ledger, accounting]
---

# ADR-25 — the current account is an immutable ledger

Rules only; content lives in [[FEEDLOT-DATA-MODEL]] and [[FEEDLOT]].

1. A client's current account is a ledger of immutable `LedgerEntry` rows. An entry is
   never edited and never deleted. A mistake is corrected by a new entry (a counter-entry
   or a `concept=adjustment`) — the account never rewrites its past.
2. The account balance is DERIVED as Σ debits − Σ credits. Sign: a positive balance means
   the client owes. `Account.balance_cached` is a denormalized read cache recomputed from
   the entries; it is never the source of truth.
3. Every debit snapshots the `unit_price` and `quantity` of the day it was posted. A later
   price change never alters an existing entry — historical price is permanent. The account
   is denominated in ARS.
4. Feed costing by origin. A `FeedingEvent` with `origin=own_stock` posts a `debit`
   (`quantity × unit_price`) AND an `out` `FeedStockMovement` on own stock. A
   `FeedingEvent` with `origin=client_stock` posts ONLY the `out` movement on the client's
   stock and NO ledger entry — the client already provided that feed. Consumption metrics
   value both origins; billing charges only own stock. Billing and the consumption metric
   are distinct and MUST NOT be conflated.
5. On `origin=client_stock` shortfall, the default policy is: serve the available quantity
   from the client's stock (uncharged) and the remainder from own stock as a charged split
   (two movements, one debit for the own-stock part). An alternative "block and warn"
   policy is permitted only if fixed here by the owner; until then the split is the rule.
   (Owner confirmation pending.)
6. `HealthEvent` always posts a `debit` — vaccines and treatments are feedlot inputs.
   `Intake`, `Weighing`, `Death` post no ledger entry. `Exit` posts no ledger entry in the
   initial phases; sale settlement is a later addition and MUST arrive as its own ADR.
7. A `Payment` posts a `credit` `LedgerEntry` that reduces the total balance; the initial
   phases do NOT imputes a payment against specific charges. Explicit payment-to-charge
   imputation, if needed, is a later addition with its own model — never by mutating entries.
8. Every charge-bearing entry carries `(source_kind, source_id)` back to its originating
   event ([[adr-24-feedlot-domain]] rule 4), so any charge is traceable to the fact that
   produced it and vice versa.
