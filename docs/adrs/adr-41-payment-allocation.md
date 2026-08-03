---
title: adr-41-payment-allocation
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, ledger, payment, allocation, imputation, phase-4a]
---

# ADR-41 — allocation of payments to charges

**Context:** implements the item [[adr-25-account-ledger]] rule 7 explicitly deferred
("Explicit payment-to-charge imputation, if needed, is a later addition with its own model —
never by mutating entries"). It is an **addition**, not a supersession: rule 7 remains true —
the allocation arrives with its own model and never mutates an entry. Rules only; the entities
live in [[FEEDLOT-DATA-MODEL]].

## Context

The ledger (adr-25) records debits (charges) and credits (payments) and derives the total
balance as Σ debits − Σ credits. A `Payment` posts a credit that lowers the **total** balance,
but so far nothing says *which charges* that payment settled. Rule 7 foresaw that if one day
that allocation is needed, it enters with its own model, without touching the entries. This
phase builds it.

## Decisions

### 1. The allocation is its own model and does NOT touch any entry

`PaymentAllocation` links a `Payment` to a **debit** `LedgerEntry` with an `amount`. It is not
a `LedgerEntry`, it posts nothing to the ledger and it does not move the total balance — that
already moved when the payment posted its credit (adr-25 rule 7). It is a bookkeeping note
saying "of this payment, this much settles this charge". No `LedgerEntry` is ever edited or
deleted (adr-25 rule 1, intact).

*Why:* the total balance is one thing (Σ debits − Σ credits, adr-25 rule 2) and allocation to
charges is another. Mixing them — for instance by lowering a debit's `amount` when it is
collected — would rewrite the past, exactly what the ledger doctrine forbids.

### 2. The allocation is validated, and never over-allocates

`impute_payment` rejects, in the **service**: an `entry` that is not a debit of the payment's
own account; a non-positive `amount`; an allocation that would make a payment's allocated total
exceed its `amount`; or one that would make the amount allocated against a debit exceed the
debit's `amount`. A `LedgerEntry` and a `Payment` from different accounts are not allocated to
each other.

*Why:* a payment cannot settle more than it is, nor can a charge end up settled beyond its
value. The validation lives in the service, the single write point, so that view, admin and
command share the same rule.

### 3. The default policy is FIFO; an explicit one wins

`auto_impute_payment_fifo` allocates a payment against the account's outstanding debits, oldest
to newest, until the payment or the charges run out. It is the default policy and it is
declared here (it is not left "pending confirmation" like the feed split of adr-25 rule 5). An
explicit allocation — a list of `(entry, amount)` — takes priority and is used when the
operator decides a different split.

*Why:* fixing the default policy in the ADR keeps each caller from inventing its own. FIFO is
the usual accounting convention (the oldest charge is settled first) and it is auditable; the
explicit path covers the case where the business wants something else.

### 4. The outstanding amount per charge is a derivation, not a field

`outstanding_charges(account)` derives, for each debit of the account, how much was allocated
to it (Σ `PaymentAllocation.amount`) and how much remains outstanding (`amount` − allocated).
No `paid` or `outstanding` field is stored on `LedgerEntry`.

*Why:* the same discipline as the balance (adr-25 rule 2): the outstanding amount is derived
from the facts, never denormalized as editable truth. A mutable `paid` field would drift out of
sync with the allocations.

### 5. The allocation is an immutable fact: it is created and read

`PaymentAllocation` exposes `list`/`retrieve`/`create` — without `update` or `destroy` (adr-49
rule 3). A mistaken allocation is corrected with another allocation (a counter-allocation with
a negative `amount` offsets it), never by editing the row. The explicit counter-allocation, if
needed, is a future addition with its own change — this phase delivers the positive allocation.

*Why:* the same event-sourced posture as the rest of the system. A dated fact is not rewritten.

## Consequences

- The backend enters only through [[API]] (adr-03) and is born through the [[TDD]] flow
  (adr-07).
- `PaymentAllocation` is the only new model; `LedgerEntry`, `Payment` and the balance are not
  refactored. The allocation composes on top of the ledger, it does not reform it.
- The client's total balance does **not** change by allocating: allocating is classifying an
  already-posted credit against charges, not charging again. A client with balance 0 and all
  their charges allocated, and one with balance 0 and nothing allocated, owe the same total.
- Any change to rules 1–5 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
