---
title: adr-25-account-ledger
type: adr
category: backend
use_case: posting a charge or a payment, reading a balance, costing feed by origin, adding an event that touches a client's account
created: 2026-07-21
modified: 2026-08-02
tags: [adr, feedlot, ledger, accounting]
---

# ADR-25 — the current account is an immutable ledger

## CONTEXT

> A client's account is a list of entries that are never edited and never deleted. The balance is derived from them, the price of the day is frozen into each one, and a mistake is corrected by another entry.

## ASSERTIONS

1. A client's current account is a ledger of immutable `LedgerEntry` rows. An entry is never edited and never deleted; a mistake is corrected by a new entry — a counter-entry, or one with `concept=adjustment`.
2. The balance is derived as Σ debits − Σ credits, and a positive balance means the client owes. `Account.balance_cached` is a read cache recomputed from the entries and is never the source of truth.
3. Every debit snapshots the `unit_price` and `quantity` of the day it was posted. A later price change never alters an existing entry — the historical price is permanent. The account is denominated in ARS.
4. Feed costs by origin. A `FeedingEvent` with `origin=own_stock` posts a `debit` of `quantity × unit_price` and an `out` `FeedStockMovement` against own stock. One with `origin=client_stock` posts only the `out` movement against the client's stock and no ledger entry — the client already provided that feed. Consumption metrics value both origins; billing charges only own stock, and the two are never conflated.
5. On a `client_stock` shortfall the served quantity splits: what the client's stock covers is served uncharged, the remainder comes from own stock as a charged split — two movements, one debit for the own-stock part.
6. `HealthEvent` always posts a `debit`: vaccines and treatments are feedlot inputs. `Intake`, `Weighing` and `Death` post nothing. An `Exit` posts nothing except a sale, which settles under [[adr-43-sale-settlement]].
7. A `Payment` posts a `credit` that reduces the total balance. Imputing a payment against specific charges is a separate record ([[adr-41-payment-allocation]]) and never a mutation of an entry.
8. Every charge-bearing entry carries `(source_kind, source_id)` back to the event that produced it ([[adr-24-feedlot-domain]] rule 4), so a charge is traceable to its fact and a fact to its charge.

## FORBIDDEN

- **NEVER** edit or delete a `LedgerEntry` (rule 1). The account's value is that its past cannot move; a correction that rewrites history leaves nothing to audit.
- **NEVER** read `balance_cached` as the truth (rule 2). It is derived, and a cache consulted as a source is a balance nobody can recompute.
- **NEVER** reprice an existing entry (rule 3). The entry records what was charged that day, not what the same input would cost now.
- **NEVER** charge feed the client provided (rule 4). The `client_stock` origin exists to move stock without touching the account.
- **NEVER** conflate the consumption metric with billing (rule 4). Both origins are eaten; only one is owed.
- **NEVER** lower a debit to reflect a payment (rules 1, 7). The payment is its own credit, and its imputation is its own record.

## REJECTED

- **Storing the balance as an editable field** — a number on the account, written on each post. Rejected because it can disagree with the entries and, once it does, there is no way to tell which is wrong. Rule 2 keeps it a cache.
- **A per-charge foreign key on the entry** — a column per charging event type. It lost to the generic `(source_kind, source_id)` pair ([[adr-24-feedlot-domain]] rule 4), which lets a new domain charge without migrating `ledger`.
- **Blocking a feeding on a `client_stock` shortfall** — refusing the event and warning the operator instead of splitting it. Weighed against rule 5 and not taken: the ration was served, and an event the system refuses to record is a fact that leaves the system entirely. It would reopen only if the owner decided a shortfall must halt the operation.
- **`Exit` never settling** — the policy this ADR held until [[adr-43-sale-settlement]] arrived, when a sale left no economic trace and `sale_price_per_kg` was informative only. Replaced, as rule 6 always required, by an ADR of its own rather than by a change here.
- **Payments that impute against nothing** — the initial policy, where a credit moved the total balance and no record said which charges it settled. Replaced by [[adr-41-payment-allocation]], which adds the imputation as its own model without touching an entry.

## RELATED

### related adrs

- [[docs/adrs/adr-24-feedlot-domain]] — rule 4, the `(source_kind, source_id)` seam
- [[docs/adrs/adr-41-payment-allocation]] — the imputation rule 7 defers to
- [[docs/adrs/adr-43-sale-settlement]] — the settlement rule 6 defers to
- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — why a death reverts no charge
- [[docs/adrs/adr-29-metrics-derivation]] — rule 4, payments are not costs

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `LedgerEntry`, `Account`, `FeedStockMovement`, `Payment`
- [[docs/FEEDLOT]] — how the account reads against the operation
