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

1. HTMX is in the stack, pinned in [[REQUIREMENTS]] like every other package ([[adr-50-initial-stack]] rule 1). It is rung 2 of the interactivity ladder ([[adr-52-frontend-and-design-system]] rule 3). Prefer it over a Svelte island whenever the state is server-owned; criteria in [[HTMX]].
2. Django generates fragment HTML. Astro only loads the client and places `hx-*` attributes. Domain fragments are not produced by Astro or Svelte. Detail: [[HTMX]], [[BACKEND]].
3. Fragment routes are endpoints, and [[adr-51-api-and-backend]] rule 4 is where that is decided — this ADR adds nothing to it and states no second version of it.
4. Using HTMX is decided per feature against [[HTMX]]'s criteria — never "every page must be HTMX".
5. Reserved. The version pin is [[adr-50-initial-stack]] rule 1, cited from rule 1 above.
6. Fragment caching follows [[CACHE]]; rendered fragment text follows [[LOCALIZATION]] — attributes, IDs, and paths stay English.
7. Backend design for HTMX (templates, CSRF, `HX-*` headers, HTML error fragments) is mandatory from the first plan of a server-owned interactive feature — not a retrofit after the JSON API.

## FORBIDDEN

- **NEVER** produce a domain fragment in Astro or Svelte (rule 2). Django generates the HTML; the client only wires the attribute.
- **NEVER** wire an `hx-*` attribute at a route absent from [[API]] ([[adr-51-api-and-backend]] rule 4). A fragment route living only in a template is a shadow route, invisible to the contract.
- **NEVER** decide "every page is HTMX" as a blanket policy instead of a per-feature call (rule 4). Escalation is a decision, not a default.
- **NEVER** design the JSON API first and retrofit HTMX after (rule 7). CSRF, `HX-*` headers, and HTML error fragments are part of the first plan of a server-owned feature.

## REJECTED

- **A Svelte island for server-owned state** — the alternative to rung 2, and the reason the ladder has one. It lost because it moves state the server already holds into a second place that can disagree with it, and pays hydration for markup Django can render outright. It reopens per feature, not as a policy: the per-feature call of rule 4 is where an island wins on its own merits ([[HTMX]] owns the criteria).
- **Astro or Svelte producing domain fragments** — considered because it would keep all markup in one toolchain. Rejected: the fragment is a projection of server state, so generating it anywhere but Django puts the domain's HTML outside the app that owns the domain. Closed for as long as rule 2 stands.
- **Stating the fragment-route rule here** — rules 3 and 5 each carried their own version of a rule another ADR owns, until 2026-08-02: rule 3 restated [[adr-51-api-and-backend]] rule 4, and rule 5 restated [[adr-50-initial-stack]] rule 1. Both were dropped to pointers because two statements of one rule drift, and this ADR was the copy, not the owner ([[adr-00-discipline]] rule 1). Nothing about what the project requires changed.

## RELATED

### related adrs

- [[docs/adrs/adr-52-frontend-and-design-system]] — the ladder this ADR occupies rung 2 of
- [[docs/adrs/adr-51-api-and-backend]] — rule 4, the owner of the fragment-route case rule 3 points at
- [[docs/adrs/adr-50-initial-stack]] — rule 1, the owner of the version pin

### related files

- [[docs/HTMX]] — the criteria and mechanism this ADR gives force to
- [[docs/BACKEND]] — Django-side fragment generation
- [[docs/CACHE]] — fragment caching
- [[docs/constitution/LOCALIZATION]] — English attributes, IDs, paths
- [[docs/constitution/REQUIREMENTS]] — the version pin
