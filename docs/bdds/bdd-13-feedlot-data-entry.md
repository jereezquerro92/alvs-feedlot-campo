---
title: bdd-13-feedlot-data-entry
type: bdd
status: building
created: 2026-07-23
tags: [bdd, feedlot, data-entry, mutation]
---

# bdd-13 — feedlot data entry (feeding + weighing)

## Use case

As a logged-in user with a role ([[adr-20-authorization-lobby]]), from a client's
dashboard I open `/feedlot/<id>/load/` to record two kinds of operational fact:
a **feeding** (a ration delivered to one animal or one lot) and a **weighing**
(a measured weight of one animal or one lot). Each is submitted, the backend
service posts it, and returning to `/feedlot/<id>/` shows the derived metrics
(balance, average weight, conversion) move in response. This is the write
counterpart of the read-only dashboard ([[bdd-12-feedlot-dashboard]]).

## Frontend half

**One SSR route composing two hydrated write islands.**
`src/pages/feedlot/[id]/load.astro` is a route only ([[adr-04-frontend-and-design-system]]
rule 9): it fetches on the server (client, `?client=` animals + lots, feed-types),
gates with `requireRole` ([[adr-20-authorization-lobby]] rule 1 — a role-less
session is bounced to `/`), sets `Cache-Control: no-store` ([[adr-06-cache]]
rule 4), computes a server-side `today` default, and composes the static
`FeedlotLoadView`. The two forms — `FeedingForm`, `WeighingForm` under
`src/lib/components/feedlot/` — arrive as `client:load` slots, the same
hydration seam `SessionBadge` rides; a form is rung 3 of the interactivity
ladder because it owns client-side submit state ([[adr-04-frontend-and-design-system]]
rule 3).

**ADR-22 contract.** Every one of the new components mounts with zero props and
never throws ([[adr-22-showcase-ready-components]] rule 1, enforced by
`frontend/tests/component-mount.test.ts`), and — decisively for a write surface —
performs **no mutating action on a bare mount** (rule 2): the POST fires only
from an explicit `submit`, the target/feed-type selects default empty, and the
`onsaved` callback defaults to a safe no-op. A bare `<FeedingForm />` renders an
inert, empty-optioned form and issues no request.

**Write pattern.** Each form posts with the app's session+CSRF convention:
`fetch(publicBackendUrl + path, { method:"POST", credentials:"include",
headers:{ "Content-Type":"application/json", "X-CSRFToken":
readCsrfTokenFromCookie() } })`. Target selection encodes `animal:<id>` /
`lot:<id>` and is decoded to the XOR pair the serializer requires
([[adr-26-livestock-individual-and-lot]] rule 3). A non-OK response renders the
backend's own validation message inline; a success clears the volatile field and
shows "Guardado ✓". Copy resolves through the i18n layer, Spanish values /
English keys ([[LOCALIZATION]]).

## Backend half

**No new endpoint — writes through already-existing routes.**
`POST /api/feedings/` (the `FeedingEventViewSet` create path, routing to the
`register_feeding` service) and `POST /api/weighings/` (the weighing create path,
routing to `register_weighing`). Both go through the domain services, never a raw
INSERT — the event-sourced posture ([[adr-24-feedlot-domain]] rule 3): the
service posts the ledger debit + stock movement for `origin=own_stock`, the
movement only for `origin=client_stock` ([[adr-25-account-ledger]] rule 4). The
route also reads `GET /api/feed-types/`, `GET /api/animals/?client=`,
`GET /api/lots/?client=`, `GET /api/clients/<id>/`. All pre-exist from Phases 1–2;
this feature adds no backend surface, so no [[API]] row and no `astro-drf-aws-api`
guardian change is owed by it. (The pre-existing gap — those Phase 1–2 routes
were never recorded in [[API]], [[adr-03-api-and-backend]] rule 1 — is backend
documentation debt flagged in [[bdd-12-feedlot-dashboard]], not introduced here.)

## Error handling

A validation failure (dead/sold target, missing field, XOR violation, feeding a
target that is not the client's) surfaces the backend's message inline; the form
stays filled for correction and posts nothing further until resubmitted. An
unknown client id on the route redirects back to `/feedlot/`. A role-less session
is redirected to `/?denied=1`. A network throw shows a generic retry message.

## Shadow-test spec

- Log in (dev-login) as a role-holder → open `/feedlot/2/` → click "Cargar
  datos" → `/feedlot/2/load/` renders both forms with the client's lots/animals
  and the feed-type list populated.
- Submit a `own_stock` feeding for a lot → "Guardado ✓" → return to the panel →
  the account balance and total cost have increased.
- Submit a weighing for an animal → "Guardado ✓" → the panel's average weight /
  conversion reflect the new measurement (or state their null-reason if a segment
  became non-calculable, [[adr-29-metrics-derivation]] rule 2).
- Submit a weighing for a dead animal → the backend rejection is shown inline; no
  row is created.
- A bare mount of either form (the component-mount test) issues no POST.
- A role-less authenticated session opening the route lands on `/` with the
  denied notice.
- Until a project's shadow-test runner exists, this entry may reach `building`,
  never `shipped` ([[BDD]]). Browser smoke is kodex-only ([[AGENTS]]).
