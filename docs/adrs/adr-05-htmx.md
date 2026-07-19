---
title: adr-05-htmx
type: adr
status: active
created: 2026-07-10
tags: [adr, htmx, frontend]
---

# ADR-05 — HTMX

Rules only; content lives in [[HTMX]].

1. HTMX is in the stack (pin in [[REQUIREMENTS]]). It is rung 2 of the interactivity ladder ([[adr-04-frontend-and-design-system]]). Prefer it over a Svelte island whenever the state is server-owned; criteria in [[HTMX]].
2. Django generates fragment HTML. Astro only loads the client and places `hx-*` attributes. Domain fragments are not produced by Astro or Svelte. Detail: [[HTMX]], [[BACKEND]].
3. No shadow routes. Every fragment route is declared in [[API]] with the same columns as any endpoint. A fragment route that exists only in a template attribute is invalid.
4. Using HTMX on a given feature is decided in the [[BDD]] flow — per feature, never “every page must be HTMX”.
5. The version pin lives in [[REQUIREMENTS]] and nowhere else as SSOT.
6. Fragment caching follows [[CACHE]]; rendered fragment text follows [[LOCALIZATION]] — attributes, IDs, and paths stay English.
7. Backend design for HTMX (templates, CSRF, `HX-*` headers, HTML error fragments) is mandatory from the first plan of a server-owned interactive feature — not a retrofit after the JSON API.
