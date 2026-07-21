---
title: adr-24-feedlot-domain
type: adr
status: proposed
created: 2026-07-21
tags: [adr, feedlot, domain, architecture]
---

# ADR-24 — the feedlot domain and growth by addition

Rules only; content lives in [[FEEDLOT]] and [[FEEDLOT-DATA-MODEL]].

1. The feedlot is built as domain apps on top of the template, never by editing the
   template's spine. A new capability is a new app and its [[API]] rows ([[PRD]] "grows
   by addition"). The cattle domain is `livestock`, `feed`, `health`; the shared spine
   it rides on is `clients`, `ledger`, `market`, `advisors`.
2. App and model names are decided in [[GLOSSARY]] before first use
   ([[adr-01-glossary-and-localization]]); the additions are staged in
   `GLOSSARY-feedlot-additions.md`. The animal-health app MUST NOT collide with the
   template's existing `/api/health/` liveness surface — resolve the name before code.
3. Operational facts are immutable, dated event records; states (animal status, lot
   counts) and balances are DERIVED from them, never stored as the editable truth.
   Catalogs (`FeedType`, `HealthProduct`, `MarketSource`, `Advisor`) are the only
   editable tables. Corrections are new events, never in-place mutation.
4. Costing is generic: a charge-bearing event links to the account through a
   `(source_kind, source_id)` pair on [[adr-25-account-ledger]]'s `LedgerEntry`, not
   through a per-domain foreign key. Any future domain posts charges through that same
   pair without changing `ledger`. This pair is the sanctioned scalability seam.
5. Every fact is stated once. The business narrative is the Claude Project docs; the
   code-facing SSOTs are [[FEEDLOT]] (domain) and [[FEEDLOT-DATA-MODEL]] (entities). An
   ADR states rules and links these; it never inlines their facts (ADR-00 rule 1).
6. Backend work enters only through [[API]] ([[adr-03-api-and-backend]]) and is born via
   the [[TDD]] flow along the development loop ([[adr-07-development-flow]]); this ADR
   grants no exception to that path.
