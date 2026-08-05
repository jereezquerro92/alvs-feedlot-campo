---
title: adr-41-payment-allocation
type: adr
category: backend
use_case: allocate a payment against charges, read the outstanding amount per charge, correct a wrong allocation
created: 2026-07-25
modified: 2026-08-04
tags: [adr, feedlot, ledger, payment, allocation, imputation, phase-4a]
---

# ADR-41 — Payment Allocation Against Charges

## CONTEXT

> Which charges a payment settled. The credit already moved the total balance when it was posted; the allocation is a separate annotation that classifies that credit against the debits, without touching a single ledger entry.

## ASSERTIONS

1. `PaymentAllocation` links a `Payment` to a debit `LedgerEntry` with an `amount`. It is not a ledger entry, it does not post to the ledger, and it does not move the total balance —that already moved with the payment credit ([[adr-25-account-ledger]] rule 7)—. No `LedgerEntry` is edited or deleted ([[adr-25-account-ledger]] rule 1).
2. `impute_payment` rejects in the service: an `entry` that is not a debit of the same account as the payment, a non-positive `amount`, an allocation that would cause a payment's allocated total to exceed its amount, and one that would cause the allocated total against a debit to exceed its amount.
3. The default policy is FIFO: `auto_impute_payment_fifo` allocates against outstanding debits from oldest to newest, until the payment or the charges are exhausted. An explicit allocation —a list of `(entry, amount)`— takes precedence when the operator decides on a different distribution.
4. `outstanding_charges(account)` derives for each debit how much has been allocated to it and how much remains outstanding. No `paid` or `outstanding` field is stored on `LedgerEntry`, the same discipline as the balance ([[adr-25-account-ledger]] rule 2).
5. `PaymentAllocation` exposes `list`/`retrieve`/`create`, no `update` or `destroy` ([[adr-24-feedlot-domain]] rule 3). A wrong allocation is corrected with another allocation, never by editing the row.
6. Allocating does not change the total balance: it is classifying an already-posted credit, not charging again. A client with a zero balance and all charges allocated, and another with a zero balance and nothing allocated, owe exactly the same amount.

## FORBIDDEN

- **NEVER** reduce the `amount` of a debit when collecting it (rule 1). It rewrites the past, which is precisely what the ledger doctrine prohibits.
- **NEVER** allocate across different accounts (rule 2). One client's payment does not settle another client's charge.
- **NEVER** over-allocate a payment or a charge (rule 2). A payment cannot settle more than its amount, nor can a charge be settled above its value.
- **NEVER** store a `paid` or `outstanding` field (rule 4). It falls out of sync with the allocations as soon as one is added.
- **NEVER** edit an allocation (rule 5). The correction is another allocation.

## REJECTED

- **Allocating by mutating the debit** — subtracting from the charge what is being paid. Flatly rejected by rule 1: it would be the ledger rewriting itself.
- **Leaving the default policy unfixed** — letting each caller choose its allocation order. Rejected by rule 3: fixing FIFO in the ADR prevents multiple implicit and unauditable policies from appearing.
- **Explicit counter-allocation in this cut** — a mode for voiding an allocation with a dedicated negative amount. Deferred: this phase delivers positive allocation and the correction enters with its own change.

## RELATED

### related adrs

- [[docs/adrs/adr-25-account-ledger]] — rules 1, 2, and 7, the immutable entry, the derived balance, and the payment
- [[docs/adrs/adr-24-feedlot-domain]] — rule 3, the immutable fact
- [[docs/adrs/adr-29-metrics-derivation]] — rule 4, why a payment is not a cost

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `PaymentAllocation`, `Payment`, `LedgerEntry`
- [[docs/API]] — the allocation and outstanding-per-charge routes
