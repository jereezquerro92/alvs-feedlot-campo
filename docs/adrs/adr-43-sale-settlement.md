---
title: adr-43-sale-settlement
type: adr
status: active
created: 2026-07-26
tags: [adr, feedlot, ledger, livestock, sale, settlement, phase-4c]
---

# ADR-43 — the sale settlement: fattening commission and own-cattle sale

**Context:** fulfils the item [[adr-25-account-ledger]] rule 6 explicitly deferred (*"`Exit`
posts no ledger entry in the initial phases; sale settlement is a later addition and MUST
arrive as its own ADR"*). It is an **addition**: rule 6 is honoured to the letter — the
settlement arrives as its own ADR and never mutates an existing entry
([[adr-25-account-ledger]] rule 1). It amends the portion of
[[adr-28-animal-lifecycle-and-sanitary]] decision 3 that said "the sale is the client's, not the
feedlot's" — an in-place amendment, with the owner's consent given in conversation
([[adr-00-adr-doctrine]] rule 4b); deaths still do not touch the ledger, that part does not
change. Rules only; the entities live in [[FEEDLOT-DATA-MODEL]].

## Context

An exit (`Exit`) of kind sale closes the animal's or the lot's life in the feedlot, but so far
it left no economic trace: `sale_price_per_kg` was informative and posted nothing. The owner
defined the missing commercial model, and there are **two distinct cases**, told apart by whose
the cattle are (`Client.kind`):

- **Client cattle (`kind=boarding`).** The animal is the client's; the feedlot only fattened it.
  The client sells and collects the sale; the feedlot charges a **fattening commission** — a
  percentage on what the animal gained while it was in the feedlot.
- **Own cattle (`kind=own`).** The animal is the feedlot's. The sale is the feedlot's: the
  proceeds are own revenue offsetting the costs already accumulated in the own account.

They are two distinct entries, against two distinct kinds of account. The system tells them
apart by `Client.kind`, not by a separate field the operator has to remember.

## Decisions

### 1. The settlement is a new entry, and never mutates what exists

Settling a sale posts **one new `LedgerEntry`** to the account of the cattle's owner. It does
not edit or delete any previous entry, does not reopen the feed or sanitary charges already
posted (those stay charged) and does not rewrite the exit ([[adr-25-account-ledger]] rule 1,
intact). The entry is tied to the exit by the generic pair `(source_kind="exit",
source_id=<Exit.id>)` ([[adr-49-domain-layer-and-growth-by-addition]] rule 4), so that the
settlement is traceable to the fact that produced it.

*Why:* the same event-sourced discipline as the whole system. A settlement is a new fact, not a
correction of the past.

### 2. Client cattle: the fattening commission as a DEBIT

A sale-exit of an animal or lot belonging to a `Client(kind=boarding)` posts a **debit**
`concept=service` to the client's account, for the **fattening commission**:

```
commission = (engorde_commission_pct / 100) × kilos_gained × sale_price_per_kg
```

`kilos_gained` are the kilos the target gained inside the feedlot, measured weighing to
weighing over the measurable stretches (the same honest cut as `kilos_gained`,
[[adr-29-metrics-derivation]] rule 3, [[adr-28-animal-lifecycle-and-sanitary]] rule 2). The
entry **snapshots** the day's `unit_price` (= `sale_price_per_kg`) and `quantity` (= kilos
gained) ([[adr-25-account-ledger]] rule 3): a later price change never alters an
already-settled commission.

*Why:* the sale is the client's; the feedlot does not record the sale price as own revenue.
What the feedlot charges for boarding is the service of fattening, and the owner fixed it as a
percentage on the kilos gained valued at the sale price — not on the total weight, which
includes the entry weight the client already brought in.

### 3. Own cattle: the proceeds as a CREDIT in the own account

A sale-exit of an animal or lot belonging to a `Client(kind=own)` posts a **credit**
`concept=sale` to the own account, for the sale proceeds:

```
proceeds = weight × sale_price_per_kg
```

where `weight` is the sold weight recorded on the exit. Since the own account already
accumulates the feed and sanitary costs of the own cattle as debits, the sale credit offsets
them: the own account's net balance tends toward the **margin** (proceeds − costs). The entry
snapshots the day's `unit_price` (= `sale_price_per_kg`) and `quantity` (= `weight`)
([[adr-25-account-ledger]] rule 3).

*Why:* the sale of own cattle is indeed feedlot revenue. Recording it as a credit in the same
account that carried the costs leaves the margin legible without inventing a separate income
statement the ledger does not model today. The sign is the right one: a credit lowers the
balance (adr-25 rule 2, a positive balance = owed), and own revenue reduces what the own
account "owes" against its costs.

### 4. Honest cut: with no measurable input, nothing is posted

The settlement is optional and **gated by its inputs**. No entry is posted when:

- `sale_price_per_kg` is missing (there is no price to value with), or
- in the boarding case, `engorde_commission_pct` is missing or the kilos gained are not
  measurable / come out zero or negative (the same gap as `kilos_gained`,
  [[adr-29-metrics-derivation]] rule 2), or
- in the own case, `weight` is missing.

In those cases the exit is recorded just as before, with no settlement — never a filler charge
over data that is not there. An invented charge over a lot with no weighings reads as real
management and can justify a money decision; the explicit gap says what is missing to measure.

*Why:* the metrics doctrine forbids manufacturing a number when the inputs are missing
([[adr-29-metrics-derivation]] rule 2). A manufactured entry is worse than a manufactured
metric: it moves a client's real balance.

### 5. Deaths and transfers do not settle; only the sale does

The settlement applies **exclusively** to `Exit.kind=sale`. A death (`Death`) still does not
touch the ledger — that part of [[adr-28-animal-lifecycle-and-sanitary]] decision 3 stays
intact. An exit of `kind=transfer` or `other` (withdrawal without sale) posts nothing either:
there was no sale to settle. Consumption already charged is not reversed by an exit, just as it
was not reversed by a death.

*Why:* the amendment to adr-28 decision 3 is surgical — it changes only "the sale is the
client's, not the feedlot's" for the sale case, and does not touch the rule that deaths and
withdrawals generate no entry.

### 6. The distinction is derived from `Client.kind`, not from a new field on the event

Which entry is posted (commission-debit vs sale-credit) is decided by the `Client.kind` of the
cattle's owner, resolved from the exit's `Animal`/`Lot`. The exit gains a single new field,
`engorde_commission_pct` (nullable), which applies only to the boarding case; own cattle ignore
it. No "settlement mode" redundant with `kind` is added.

*Why:* `Client.kind` already exists and already distinguishes boarding from own cattle.
Duplicating that distinction on the event invites the two fields to contradict each other.

## Consequences

- The backend enters only through [[API]] ([[adr-03-api-and-backend]]) and is born through the
  [[TDD]] flow ([[adr-07-development-flow]]); this ADR grants no exception to that path.
- The new models are minimal: an `engorde_commission_pct` field on `Exit` and a `Concept.SALE`
  in `ledger`. There is no `Settlement` table — the settlement **is** a `LedgerEntry`, not a
  separate model.
- `register_exit` gains the settlement logic, gated; exits already loaded without a settlement
  stay valid (the settlement applies forward, it does not reprocess the past). Re-settling an
  old exit, if needed, is an explicit future action with its own change.
- A boarding client's balance goes up by the commission (one more service charge); the own
  account's balance goes down by the sale credit (the margin becomes legible).
- Any change to rules 1–6 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
