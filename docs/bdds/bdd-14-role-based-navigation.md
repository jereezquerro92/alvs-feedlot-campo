---
created: '2026-07-27'
status: draft
tags:
- bdd
- auth
- rbac
- roles
- feedlot
title: bdd-14-role-based-navigation
---

# bdd-14 — role-based navigation and the lot-owner portal

## Use case

As a **lot owner** (`lot_owners`, a client-portal session — [[GLOSSARY]], [[adr-44-field-operational-roles]] decision 3), when I sign in I land directly on **my own client's** feedlot dashboard — the metrics of my cattle and what I owe the feedlot — and I never see the client roster, another client's data, or any data-entry page. As **field staff** (`field_managers`, `feed_operators`, `field_admins`, `feedlot_owners`, `workshop`, `admins`), the roster and every client's pages open normally, subject to each route's own permission class ([[API]]). This is UX scoping layered on top of the backend boundary — the backend (`ClientScopedReadPermission`, [[adr-44-field-operational-roles]]) remains the security gate; the frontend only spares a portal session fetches it would be `403`'d on and lands it where it belongs.

## Scenarios

### A lot owner lands on its own client dashboard, never the roster

```gherkin
Given a signed-in user whose only Group is `lot_owners`
And whose `AccessRequest.client` is bound to client 7 (surfaced as `me.client` on `GET /api/me/`, [[API]])
When they request `/feedlot/` (the roster)
Then they are redirected to `/feedlot/7` — their own client dashboard ([[adr-44-field-operational-roles]] decision 3)
And the roster fetch (`GET /api/clients/`) is never issued from that request
```

### A lot owner cannot open another client's pages

```gherkin
Given a `lot_owners` session bound to client 7
When they request `/feedlot/9`, `/feedlot/9/ledger`, or `/feedlot/9/outstanding` by URL
Then they are redirected to `/feedlot/7` — a portal session may view only its own client ([[adr-44-field-operational-roles]] decision 3)
And even if the redirect were bypassed, the backend returns 403/404 for client 9's data (the real boundary)
```

### An unbound lot owner fails closed to the lobby

```gherkin
Given a `lot_owners` session whose `AccessRequest.client` is still null (`me.client` is null)
When they request `/feedlot/` or any `/feedlot/{id}` page
Then they are redirected to `/?denied=1` — the lobby, never "all clients by default" ([[adr-44-field-operational-roles]] decision 4)
```

### A lot owner never reaches a data-entry or scheduling page

```gherkin
Given a `lot_owners` session bound to client 7
When they request `/feedlot/7/load` (data entry) or `/feedlot/7/schedule` (sanitary scheduling)
Then they are redirected to `/feedlot/7` — a portal session is read-only ([[adr-44-field-operational-roles]] decision 3)
And every write the page would attempt is a POST the backend rejects for that session anyway
```

### Staff is unscoped

```gherkin
Given a signed-in user in any staff Group (e.g. `field_managers` or `feedlot_owners`)
When they request `/feedlot/` and any `/feedlot/{id}` or its sub-pages
Then the roster and each client's pages render normally, gated only by each route's own permission class ([[API]])
And a user who is BOTH `lot_owners` and a staff Group is treated as staff — the wider view wins, matching the backend
```

## Frontend half

Extends the existing feedlot pages ([[FRONTEND]], [[bdd-12-feedlot-dashboard]], [[bdd-13-feedlot-data-entry]]); it widens their SSR guard, it does not replace it. Each page already reads `GET /api/me/` and runs the lobby gate `requireRole` ([[adr-20-authorization-lobby]] rule 1, [[bdd-08-authorization-lobby]]); this entry adds a second server-side check right after it, from `frontend/src/lib/authGate.ts`:

- `portalLanding(me)` on `/feedlot/` (the roster) — a portal session is redirected to `/feedlot/{me.client.id}`, or the lobby when unbound.
- `requireClientScope(me, id)` on the client-scoped **read** pages (`/feedlot/{id}`, `.../ledger`, `.../outstanding`) — a portal session viewing any id but its own is redirected to its own.
- `denyPortalSession(me)` on the **write/ops** pages (`.../load`, `.../schedule`) — a portal session is redirected to its own dashboard.

The Group-name constants and `isPortalSession(me)` live in `frontend/src/lib/auth.ts`, mirrored from the backend Group names for UI gating only ([[adr-44-field-operational-roles]] — "el gateo es conveniencia, no la barrera"). All checks are server-rendered decisions read once on page render (rung 1 of the interactivity ladder, [[adr-04-frontend-and-design-system]]); no HTMX fragment, no island, no `PUBLIC_*` variable added ([[VARIABLES]]).

## Backend half

**No new [[API]] row and no new backend behavior** — the boundary already shipped with [[adr-44-field-operational-roles]]: the six Groups, `ClientScopedReadPermission`, and `AccessRequest.client`, all exercised by `backend/apps/users/test_roles.py`. This entry consumes the already-declared `GET /api/me/` `client` field (id, name, kind — added for exactly this UI scoping, [[adr-44-field-operational-roles]] consequence) and `groups` field ([[API]]). The frontend gating cannot widen access: every route it hides is a route the backend independently gates.

## Error handling

A portal session hitting the roster or a foreign client's page is **redirected**, never shown a `403` page — the correct landing point for "out of your scope" is your own dashboard, and for an unbound session it is the lobby ([[adr-44-field-operational-roles]] decision 4). A staff session is never redirected by these checks. If `GET /api/me/` fails at SSR, `me` is null and the pre-existing `requireRole` bounce to `/accounts/login/` applies ([[AUTH]]) — the portal checks never run on a null session. All authenticated responses stay `no-store` ([[CACHE]], [[adr-06-cache]] rule 4).

## Shadow-test spec

- Sign in as a `lot_owners`-only user bound to client 7 → land on `/feedlot/7` → `GET /feedlot/` redirects to `/feedlot/7`, roster never rendered.
- As that user, request `/feedlot/9`, `/feedlot/9/ledger`, `/feedlot/9/outstanding` → each redirects to `/feedlot/7`.
- As that user, request `/feedlot/7/load` and `/feedlot/7/schedule` → each redirects to `/feedlot/7`.
- Unbind the user (`AccessRequest.client` null) → `/feedlot/` and `/feedlot/7` both redirect to `/?denied=1`.
- Sign in as a `field_managers` user → `/feedlot/` renders the roster, `/feedlot/9` and every sub-page open normally.
- Sign in as a user in BOTH `lot_owners` and `field_managers` → treated as staff, roster renders.
- Frontend verification runs through `bun test` and the browser smoke path ([[FRONTEND]], [[BDD]]) — smoke is a `kodex`-only interactive action and does not run in an agent context ([[AGENTS]]). Until a project's shadow-test runner exists, this entry may reach `building`, never `shipped` ([[BDD]]).
