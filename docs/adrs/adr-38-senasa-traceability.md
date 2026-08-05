---
title: adr-38-senasa-traceability
type: adr
category: backend
use_case: load an establishment or its RENSPA, register a DT-e, tag an animal with a caravana, read caravana coverage
created: 2026-07-25
modified: 2026-08-04
tags: [adr, feedlot, traceability, senasa, renspa, dte, caravana, phase-11]
---

# ADR-38 — SENASA Traceability: RENSPA, DT-e, and caravana

## CONTEXT

> Livestock movement is documented with SENASA: each establishment has its RENSPA, each transit its DT-e, and each animal its caravana. The `traceability` app records those three facts without touching `livestock` or the ledger.

## ASSERTIONS

1. `Establishment` —an establishment with its `renspa`— is an editable catalogue with full CRUD. `TransitDocument` and `Caravana` are dated facts: `list`/`retrieve`/`create`, no `update` or `destroy` ([[adr-24-feedlot-domain]] rule 3); a correction or re-identification is a new record.
2. `TransitDocument` records `dte_number`, origin and destination as FK to `Establishment`, date, `category`, `head_count`, and optionally the `lot` that travelled. It does not post a ledger entry: a transit is a sanitary documentary fact, not a charge.
3. `register_transit` rejects in the service —not in the view— an inactive establishment at origin or destination, a non-positive `head_count`, an origin equal to the destination, and a duplicate `dte_number`. Late loading with a retroactive date is accepted.
4. `Caravana` links a unique `official_number` —unique at the database level— to an `Animal`, with its `assigned_date`. It is registered on an active animal; a dead, sold, or departed animal cannot be tagged.
5. `apps.metrics` derives `caravana_coverage`: for a client's active livestock, how many head have a caravana and how many do not. With no active animals it returns `null` with its reason, never a zero ([[adr-29-metrics-derivation]] rule 2).
6. `livestock` is not refactored: `Caravana` references the existing `Animal` and does not add a field to it ([[adr-32-multi-rubro-assets]] rule 2). The app adds no environment variables: there is no integration with the SENASA system in this cut.

## FORBIDDEN

- **NEVER** duplicate an `official_number` (rule 4). The caravana is permanent individual identity, and duplicating it breaks the traceability it exists to guarantee.
- **NEVER** post a ledger entry for a transit (rule 2). The DT-e is traceability, not economics; linking it to the ledger conflates two distinct questions.
- **NEVER** edit an issued DT-e or a placed caravana (rule 1). They are facts; the correction is a new record.
- **NEVER** validate the transit in the view (rule 3). The rule lives in the service, which view, admin, and command all share.
- **NEVER** report 0% coverage when there is no active livestock (rule 5). They are opposite situations and a zero conflates them.

## REJECTED

- **A `caravana` field on `Animal`** — the official identification as a column on the animal. Rejected by rule 6: the extraction looks forward and `livestock` is not touched; the dated record also preserves when it was placed.
- **Integrating DT-e issuance or lookup with SENASA** — talking to the real system. Explicitly out of scope for this cut, which records the document; integration enters as a future addition with its own change.
- **Re-tagging due to tag loss** — a flow for replacing a caravana. Not modelled in this phase; enters explicitly when the case arises, not as a side effect of the uniqueness constraint.

## RELATED

### related adrs

- [[docs/adrs/adr-24-feedlot-domain]] — rule 3, editable catalogue and immutable event
- [[docs/adrs/adr-33-feedyard-operating-loop]] — rule 5, the same catalogue/event precedent
- [[docs/adrs/adr-32-multi-rubro-assets]] — rule 2, the forward extraction
- [[docs/adrs/adr-29-metrics-derivation]] — rule 2, the honest gap in coverage

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `Establishment`, `TransitDocument`, `Caravana`
- [[docs/GLOSSARY-feedlot-additions]] — RENSPA, DT-e, caravana
- [[docs/API]] — the traceability routes
