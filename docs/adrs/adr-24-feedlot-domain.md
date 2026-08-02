---
title: adr-24-feedlot-domain
type: adr
category: backend
use_case: adding a feedlot capability or app, deciding where a new model lives, posting a charge from a new domain, naming anything in the feedlot domain
created: 2026-07-21
modified: 2026-08-02
tags: [adr, feedlot, domain, architecture]
---

# ADR-24 — the feedlot domain and growth by addition

## CONTEXT

> The feedlot is domain apps standing on the template's spine, never an edit to that spine. Its facts are immutable events, its states are derived, and every charge reaches the account through one generic pair.

## ASSERTIONS

1. The feedlot is built as domain apps on top of the template. A new capability is a new app and its [[API]] rows ([[PRD]] — grows by addition). The cattle domain is `livestock`, `feed` and `sanitary`; the shared spine it rides on is `clients`, `ledger`, `market` and `advisors`.
2. App and model names are decided in [[GLOSSARY]] before first use ([[adr-01-glossary-and-localization]]); the feedlot additions are staged in `GLOSSARY-feedlot-additions.md`. A domain name never collides with a template surface — the animal-health domain is `sanitary` precisely because `/api/health/` is the liveness probe ([[adr-28-animal-lifecycle-and-sanitary]] rule 4).
3. Operational facts are immutable, dated event records. States — animal status, lot counts — and balances are derived from them, never stored as the editable truth. Catalogs are the only editable tables, and a correction is a new event.
4. Costing is generic: a charge-bearing event reaches the account through the `(source_kind, source_id)` pair on `LedgerEntry` ([[adr-25-account-ledger]]), never a per-domain foreign key. Any future domain posts charges through that same pair without changing `ledger`. This pair is the sanctioned scalability seam.
5. Every fact is stated once. The code-facing sources of truth are [[FEEDLOT]] for the domain and [[FEEDLOT-DATA-MODEL]] for the entities; an ADR links them and inlines nothing ([[adr-00-adr-doctrine]] rule 1).
6. Backend work enters only through [[API]] ([[adr-03-api-and-backend]]) and is born through the [[TDD]] flow along the development loop ([[adr-07-development-flow]]). No feedlot ADR grants an exception to that path.

## FORBIDDEN

- **NEVER** edit the template's spine to make room for a feedlot capability (rule 1). The spine is what every project shares; a capability that needs it changed is a capability in the wrong place.
- **NEVER** store a state or a balance as the editable truth (rule 3). The events are the record; a stored state disagrees with them the first time one is loaded late.
- **NEVER** correct an event by editing it (rule 3). The correction is another event, so the account can still show what was believed and when.
- **NEVER** add a per-domain foreign key to `LedgerEntry` (rule 4). The generic pair exists so that a new domain costs `ledger` no migration at all.
- **NEVER** use a domain name that collides with a template route (rule 2). The probe is a contract with the orchestrator and does not move.

## REJECTED

- **A single polymorphic event table for the whole domain** — every operational fact in one table with a type column. Rejected for the nullable columns it forces on every row and the type filter it forces into every query; each event keeps its own table and shares only its abstract shape ([[adr-28-animal-lifecycle-and-sanitary]] rule 1).
- **A foreign key per charging domain on `LedgerEntry`** — `feeding_event`, `health_event`, and one more with each new rubro. It read more explicitly and lost to rule 4: it would make `ledger` migrate every time an unrelated domain learned to charge.
- **`health` as the animal-health app name** — the obvious name, taken by the template's liveness surface. Renamed rather than colliding, because the probe is a contract with the orchestrator ([[adr-28-animal-lifecycle-and-sanitary]] rule 4).

## RELATED

### related adrs

- [[docs/adrs/adr-25-account-ledger]] — the ledger rule 4's pair lands on
- [[docs/adrs/adr-26-livestock-individual-and-lot]] — how cattle enter and are carried
- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — the lifecycle events and the `sanitary` name
- [[docs/adrs/adr-03-api-and-backend]] — the API-first path rule 6 keeps
- [[docs/adrs/adr-07-development-flow]] — the loop every feedlot change walks

### related files

- [[docs/FEEDLOT]] — the domain narrative
- [[docs/FEEDLOT-DATA-MODEL]] — the entities and their fields
- [[docs/API]] — the endpoint contract every app enters through
- [[docs/GLOSSARY]] — the names, decided before first use
