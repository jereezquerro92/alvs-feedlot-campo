---
title: adr-05-htmx
type: adr
category: frontend
use_case: deciding HTMX vs a Svelte island for a feature, writing a Django fragment view, wiring hx-* attributes, caching a fragment response
created: 2026-07-10
modified: 2026-08-02
tags: [adr, htmx, frontend]
---

# ADR-05 — HTMX

## CONTEXT

> HTMX is rung 2 of the ladder: Django owns the fragment, Astro only wires the attribute.

## ASSERTIONS

1. HTMX is in the stack (pin in [[REQUIREMENTS]]). It is rung 2 of the interactivity ladder ([[adr-04-frontend-and-design-system]]). Prefer it over a Svelte island whenever the state is server-owned; criteria in [[HTMX]].
2. Django generates fragment HTML. Astro only loads the client and places `hx-*` attributes. Domain fragments are not produced by Astro or Svelte. Detail: [[HTMX]], [[BACKEND]].
3. No shadow routes. Every fragment route is declared in [[API]] with the same columns as any endpoint. A fragment route that exists only in a template attribute is invalid.
4. Using HTMX on a given feature is decided in the [[BDD]] flow — per feature, never "every page must be HTMX".
5. The version pin lives in [[REQUIREMENTS]] and nowhere else as SSOT.
6. Fragment caching follows [[CACHE]]; rendered fragment text follows [[LOCALIZATION]] — attributes, IDs, and paths stay English.
7. Backend design for HTMX (templates, CSRF, `HX-*` headers, HTML error fragments) is mandatory from the first plan of a server-owned interactive feature — not a retrofit after the JSON API.

## FORBIDDEN

- **NEVER** produce a domain fragment in Astro or Svelte (rule 2). Django generates the HTML; the client only wires the attribute.
- **NEVER** wire an `hx-*` attribute at a route absent from [[API]] (rule 3). A fragment route living only in a template is a shadow route, invisible to the contract.
- **NEVER** decide "every page is HTMX" as a blanket policy instead of a per-feature [[BDD]] call (rule 4). Escalation is a decision, not a default.
- **NEVER** design the JSON API first and retrofit HTMX after (rule 7). CSRF, `HX-*` headers, and HTML error fragments are part of the first plan of a server-owned feature.

## RELATED

### related adrs

- [[docs/adrs/adr-04-frontend-and-design-system]] — the ladder this ADR occupies rung 2 of
- [[docs/adrs/adr-03-api-and-backend]] — rule 1, which rule 3 here restates as a named case

### related files

- [[docs/HTMX]] — the criteria and mechanism this ADR gives force to
- [[docs/BACKEND]] — Django-side fragment generation
- [[docs/CACHE]] — fragment caching
- [[docs/LOCALIZATION]] — English attributes, IDs, paths
- [[docs/REQUIREMENTS]] — the version pin
