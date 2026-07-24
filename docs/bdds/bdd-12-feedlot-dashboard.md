---
title: bdd-12-feedlot-dashboard
type: bdd
status: building
created: 2026-07-23
tags: [bdd, feedlot, dashboard]
---

# bdd-12 — feedlot read-only dashboard

## Use case

As a logged-in user with a role ([[adr-20-authorization-lobby]]), I can open
`/feedlot/` to see every client of the feedlot with the balance of its current
account, and click into a client to reach `/feedlot/<id>/`, a read-only panel
showing that client's derived metrics (balance, head count, average weight,
feed conversion, mortality, total cost, kilos gained), the evolution of its
account, a reference market-price series, and its herd (lots + individual
animals). Nothing on either page mutates data — this is the "ver el feedlot"
surface, distinct from the data-entry feature ([[bdd-13-feedlot-data-entry]]).

## Frontend half

**Two SSR routes, no islands beyond the session badge**
([[adr-04-frontend-and-design-system]] rule 9). `src/pages/feedlot/index.astro`
and `src/pages/feedlot/[id].astro` are routes only: they fetch on the server,
gate with `requireRole` ([[adr-20-authorization-lobby]] rule 1 — a role-less
session is bounced to `/` with a reason), set `Cache-Control: no-store`
([[adr-06-cache]] rule 4, authenticated), and compose Svelte views. No rung-2
HTMX or rung-3 island is needed: the pages are pure server-rendered reads, the
lowest rung of the interactivity ladder ([[adr-04-frontend-and-design-system]]
rule 3). Only `SessionBadge` hydrates (`client:load`), reused unchanged.

**Components** under `src/lib/components/feedlot/` — `MetricCard`, `TrendChart`
(inline SVG, token-driven colour via `currentColor`/`text-primary`),
`ClientsTable`, `HerdTable` — and two views under `src/lib/components/views/`
(`FeedlotClientsView`, `FeedlotDashboardView`). Every one mounts with zero props
and never throws ([[adr-22-showcase-ready-components]] rule 1, enforced by
`frontend/tests/component-mount.test.ts`) and performs no mutating action on a
bare mount (rule 2 — the dashboard is read-only by construction). The
null-contract is honoured in the UI: a metric that arrives `null` renders as
"—" with its reason, never a fabricated zero ([[adr-29-metrics-derivation]]
rule 2). Copy resolves through the i18n layer, Spanish values / English keys
([[LOCALIZATION]]); a "Feedlot" entry is added to the lobby nav.

## Backend half

**No new endpoint — consumes only already-declared routes.** The pages read
`GET /api/clients/`, `GET /api/clients/<id>/`, the `GET
/api/clients/<id>/metrics/{summary,account}/` derivations, `GET
/api/animals/?client=<id>`, `GET /api/lots/?client=<id>`, and `GET
/api/market-prices/?source=canuelas`. All pre-exist from Phases 1–3; the
read-only dashboard adds no backend surface, so no [[API]] row and no
`astro-drf-aws-api` guardian change is owed by this feature. (Pre-existing
defect noted separately: those Phase 1–3 routes were never recorded in [[API]]
— [[adr-03-api-and-backend]] rule 1 — which is backend documentation debt, not
introduced here.)

## Error handling

Each SSR fetch is guarded: a non-OK or thrown response yields an empty list or a
`null` metric, and every consuming component renders its own empty/"—" state
rather than throwing. An unknown client id on `/feedlot/<id>/` redirects back to
`/feedlot/`. A role-less session is redirected to `/?denied=1`.

## Shadow-test spec

- Log in (dev-login) as a role-holder → open `/feedlot/` → both demo clients
  listed with their ARS balances and a "Ver panel" link each.
- Click "Ver panel" on *Estancia La Esperanza* → `/feedlot/2/` renders metric
  tiles (conversion ≈ 7,40; mortality shown as a %), the account-evolution and
  market-price charts as SVG polylines, and the herd tables (lots + NOV-xxx
  animals).
- A metric with no measurable data renders "—" plus its reason, never `0`.
- A role-less authenticated session opening `/feedlot/` lands on `/` with the
  denied notice; an anonymous visitor is likewise bounced.
- Until a project's shadow-test runner exists, this entry may reach `building`,
  never `shipped` ([[BDD]]). Browser smoke is kodex-only ([[AGENTS]]).
