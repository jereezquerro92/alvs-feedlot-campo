---
title: HTMX
type: reference
status: active
created: 2026-07-10
tags: [harness, frontend, htmx, backend]
---

# HTMX

HTMX is **in the stack** (pin in [[REQUIREMENTS]]: `htmx.org@2.0.10`). It is rung 2 of the interactivity ladder in [[FRONTEND]]: preferred over a Svelte island whenever state is server-owned. Using HTMX on a given feature is still a per-feature decision in [[BDD]]; the library itself is not optional scaffolding.

## Core doctrine — Django owns the HTML

> [!important]
> HTMX exists in this template **because Django exists**. The browser library only swaps markup; **Django generates that markup**. Astro loads the client, places `hx-*` attributes, and never invents domain fragments for HTMX to consume.

Implications from day one of any backend design:

1. **Fragment producer = Django** — `TemplateResponse` / Django templates (`apps/<domain>/templates/…`). Not DRF JSON, not Astro SSR inventing the swap body, not Svelte rendering a fragment for `hx-swap`.
2. **Design Django for HTMX before the first `hx-get`** — views, URL rows in [[API]], template partials, CSRF, auth, and `Cache-Control` are backend work. Frontend only wires attributes to declared paths.
3. **JSON API and HTML fragments are different contracts** — same domain model may expose a DRF JSON endpoint *and* a fragment endpoint; they are separate [[API]] rows. Never return JSON and expect HTMX to “understand” it without an explicit out-of-band agreement (default: HTML only).
4. **Session/CSRF for mutations** — POST/PUT/PATCH/DELETE fragments use Django session auth + CSRF (cookie + header). Token-only SPA patterns are not the HTMX default here.

Full backend rules: [[BACKEND]]. Ladder criteria: below. Enforcement: [[adr-05-htmx]].

## Split of responsibilities

| Layer | Owns |
|---|---|
| **Django** | Fragment routes, template partials, request handling (`HX-Request`, `HX-Target`, …), response headers (`HX-Trigger`, `HX-Redirect`, `HX-Retarget`, …), authz, validation errors as HTML, caching headers ([[CACHE]]) |
| **Astro** | Loads `htmx.org` once in the document shell; places `hx-*` on server-rendered markup; never hosts a parallel fragment renderer for app domain data |
| **[[API]]** | Declares every fragment path before code exists — same table as JSON endpoints |
| **Svelte** | Only when client-owned state requires an island — not a substitute fragment engine |

## Rules

1. **No shadow routes** ([[adr-05-htmx]]): every fragment path is a row in [[API]]. A path that exists only inside an `hx-get` / `hx-post` string is invalid.
2. **Version pin** lives only in [[REQUIREMENTS]] (`htmx.org` **2.0.10**). Do not restate the number elsewhere as a second SSOT.
3. **Adoption per feature** via [[BDD]] — HTMX is available; each feature still chooses ladder rung 2 vs 3.
4. Fragment bodies are **HTML** (`text/html`), English identifiers/paths ([[LOCALIZATION]]); user-visible copy may localize at render time.
5. Caching of fragments follows [[CACHE]]; authenticated fragments default `Cache-Control: no-store`.
6. Prefer **dedicated fragment views** (or explicit branch on `HX-Request`) designed for partial HTML — do not bolt fragments onto a JSON viewset as an afterthought without an [[API]] row and tests.

## Django requirements (design from the start)

When a feature will use HTMX, the backend half must plan for:

| Concern | Expectation |
|---|---|
| Templates | Partial templates under the domain app; stable element `id`s that match `hx-target` |
| Detection | Read `HX-Request` (and related headers) when full-page and fragment share a view; prefer separate fragment endpoints when contracts differ |
| Errors | Validation / permission failures return **HTML fragments** (inline errors, forms with messages) — not bare JSON error envelopes |
| CSRF | Forms and non-GET `hx-*` include CSRF; Django middleware remains authoritative |
| Headers out | Use `HX-Trigger`, `HX-Redirect`, `HX-Push-Url`, `HX-Retarget`, `HX-Reswap` when the interaction needs them; document non-obvious ones in the [[API]] contract section |
| Auth | Same permission model as the rest of the app; prefer session for browser HTMX |
| Tests | Fragment endpoints covered under [[TDD]] (status, auth, key markup); not only JSON serializers |

Patterns: skill `kdx-django-6-drf` → `references/patterns.md` (HTMX section).

## Frontend requirements (thin)

- Bundle **htmx.org@2.0.10** with bun; load **once** in the root layout ([[FRONTEND]]).
- `hx-*` targets only paths declared in [[API]] under backend prefixes (`/api/`, …).
- Do not implement domain fragment HTML in Astro/Svelte for HTMX swaps.

## When HTMX vs when Svelte

Who owns the state:

| Signal | Use |
|---|---|
| Forms, submit-and-refresh | HTMX (Django form/fragment) |
| Lists, pagination, filtering | HTMX |
| Partial refresh of a server-rendered region | HTMX |
| Polling for server-side updates | HTMX |
| Rich widgets with local component state | Svelte island |
| Optimistic UI (act before the server confirms) | Svelte island |
| Offline or connectivity-tolerant interactions | Svelte island |
| Canvas, drag-and-drop, pointer-heavy UI | Svelte island |

Rule of thumb: server-owned state → HTMX + Django HTML; client-owned state → Svelte island. When in doubt, stay lower on the ladder in [[FRONTEND]].
