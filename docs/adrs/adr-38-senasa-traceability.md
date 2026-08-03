---
title: adr-38-senasa-traceability
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, traceability, senasa, renspa, dte, caravana, phase-11]
---

# ADR-38 — SENASA traceability: RENSPA, DT-e and ear tag

**Context:** grows by addition ([[adr-49-domain-layer-and-growth-by-addition]]): a new
`traceability` app on top of the spine, without touching `livestock` or the ledger. Reuses the
event-sourced posture of [[adr-49-domain-layer-and-growth-by-addition]] rule 3 and the "a
catalog is edited, an event is immutable" precedent of [[adr-33-feedyard-operating-loop]]
decision 5. Rules only; the entities live in [[FEEDLOT-DATA-MODEL]].

## Context

Cattle movement in Argentina is documented before SENASA: every establishment has a
**RENSPA**, every transfer of animals travels with a **DT-e** (electronic transit document)
linking an origin RENSPA to a destination one, and every animal carries its official
individual identification **ear tag** (`Caravana`). Today the system knows what an animal eats
and how much it weighs, but not where it came from nor under which document — there is no
sanitary traceability. The `traceability` app is added with those three facts.

## Decisions

### 1. The RENSPA is an editable catalog; the DT-e and the ear tag are immutable

`Establishment` (an establishment with its `renspa`) is master data: a ModelViewSet with full
CRUD — "loading establishments" is creating rows. `TransitDocument` (the DT-e) and `Caravana`
are dated facts: list/retrieve/create, without update or destroy (adr-49 rule 3). A correction
to a DT-e or a re-identification is a new record.

*Why:* an establishment has state that gets corrected (it is retired, it is renamed); an
issued transit document and a placed ear tag are facts that are not rewritten.

### 2. The DT-e links two establishments by their RENSPA, and does not touch the ledger

`TransitDocument` records `dte_number`, `origin`/`destination` (FK to `Establishment`), date,
`category`, `head_count` and optionally the `lot` that travelled. It posts no entry: a transit
is a sanitary documentary fact, not a charge. Charging remains exclusively the ledger's via
`feed` (adr-25).

*Why:* a single charging path. The DT-e is traceability, not economics; tying it to the ledger
would conflate two distinct questions.

### 3. The DT-e validates in the service, not in the view

`register_transit` rejects, in the **service**, an inactive `Establishment` at origin or
destination, a non-positive `head_count`, an origin equal to the destination and a duplicate
`dte_number`. Late entry with a retroactive date is accepted (the same field norm as adr-28).

*Why:* business rules live in the service, the single write point, so that view, admin and
command share the same validation.

### 4. The ear tag identifies an individual animal and is unique

`Caravana` links a unique `official_number` to an `Animal` with its `assigned_date`. It is
recorded when placed on an active animal; a dead/sold/departed animal is not tagged. The
uniqueness of `official_number` is enforced at the database level.

*Why:* the official ear tag is permanent individual identity; duplicating it would break the
traceability it exists to guarantee. A physical re-tagging (lost tag) is an explicit future
addition, not part of this phase.

### 5. Ear-tag coverage is a derived metric, honest about the gap

`apps.metrics` gains `caravana_coverage`: over a client's **active** cattle, how many head
have an official ear tag and how many do not. With no active animals the coverage is `null`
with its reason, never a filler zero (adr-29 rule 2).

*Why:* "0% coverage" and "there is no cattle to tag" are opposite situations; a zero conflates
them, the explicit gap distinguishes them.

## Consequences

- The backend enters only through [[API]] (adr-03) and is born through the [[TDD]] flow
  (adr-07).
- No environment variables are added: the app is internal data, with no integration with
  SENASA's system in this phase — real DT-e issuance/lookup against SENASA is an explicit
  future addition, not part of this cut.
- `livestock` is not refactored: the `Caravana` references the existing `Animal`, it does not
  add a field to `Animal` (the extraction looks forward, adr-32 rule 2).
- Any change to rules 1–5 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
