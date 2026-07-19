---
created: '2026-07-14'
status: draft
tags:
- bdd
- auth
- lobby
- rbac
title: bdd-08-authorization-lobby
type: bdd
---

# bdd-08 — authorization lobby

## Use case

As an **anonymous visitor** or a **signed-in user with no Group membership yet**, when I request any page, I land on `/` — the lobby ([[GLOSSARY]]: lobby) — and, once signed in, I see a pending-authorization legend (`lobby_pending`, [[GLOSSARY]], [[LOCALIZATION]]) until an admin grants me a role. As a **signed-in user who already holds a role**, every route opens normally and I never see the lobby's pending state.

## Scenarios

### Anonymous visitor reaches the lobby only

```gherkin
Given a visitor with no Django session
When they request any route other than `/`
Then they are redirected to `/accounts/login/` per the existing session gate ([[AUTH]])
And requesting `/` directly renders the lobby with the sign-in affordance, no legend shown
```

### Freshly signed-in, role-less user is confined to the lobby

```gherkin
Given a user who has completed Cognito login (a Django session exists)
And their `AccessRequest.role` is still null ([[GLOSSARY]]: `AccessRequest`, `role`)
When they request `/`
Then they see the `lobby_pending` legend ([[GLOSSARY]], [[LOCALIZATION]])
When they request any other route
Then they are redirected back to `/` — no `403`, the lobby is the landing point for a role-less session ([[adr-20-authorization-lobby]] rule 1)
```

### An admin grants a role

```gherkin
Given a role-less signed-in user stuck on the lobby
When an `admins` member sets `AccessRequest.role` to a Group in Django admin (`/admin/`, [[API]])
Then the `post_save` signal adds that Group to the user's `user.groups` ([[adr-20-authorization-lobby]] rule 3)
And the user's very next request — a plain refresh, no re-login — reaches their previously blocked route normally ([[adr-20-authorization-lobby]] rule 4)
```

### A role-holding user never sees the lobby's pending state

```gherkin
Given a signed-in user who is already a member of at least one Django Group
When they request `/`
Then `/` renders its normal signed-in content (the session badge, [[COMPONENTIZATION]]) — no `lobby_pending` legend
And every other route opens normally, subject only to that route's own permission class ([[API]])
```

## Frontend half

`/` is the existing home page ([[FRONTEND]]) carrying the `SessionBadge` component ([[COMPONENTIZATION]], [[AUTH]]) — this entry widens it, not replaces it: for a role-less authenticated session it additionally renders the `lobby_pending` legend, server-rendered HTML only (rung 1 of the interactivity ladder, [[adr-04-frontend-and-design-system]] — no HTMX fragment, no island; the state — `role` present or not — is read once, server-side, on page render). The legend text itself is a rendered i18n string keyed `lobby_pending` ([[GLOSSARY]], [[LOCALIZATION]]) — the Spanish value is the i18n layer's to define, not this entry's. No `PUBLIC_*` variable is added ([[VARIABLES]]).

## Backend half

Feeds [[tdd-02-access-request]]: the `AccessRequest` model, its nullable `role` field, and the `post_save` signal that mirrors a grant into `user.groups` ([[adr-20-authorization-lobby]]). **No new [[API]] row** — the admin grant path reuses the already-declared `/admin/` mount and the gate check reads Group membership through the same session Django already establishes, surfaced to the frontend via the already-declared `GET /api/me/` `groups` field ([[API]]); `api: []` in [[tdd-02-access-request]].

## Error handling

An anonymous visitor hitting a non-lobby route is redirected to `/accounts/login/`, unchanged from today's session gate ([[AUTH]]). A role-less authenticated session hitting a non-lobby route is redirected to `/` — never a `403` — since the lobby, not an error page, is the correct landing point for "not yet authorized" ([[adr-20-authorization-lobby]] rule 2). All authenticated responses stay `no-store` ([[CACHE]], [[adr-06-cache]] rule 4).

## Shadow-test spec

- Visit any route signed out → redirected to `/accounts/login/`; visit `/` directly signed out → lobby renders, no legend.
- Complete Cognito login as a brand-new user (`AccessRequest.role` null) → land on `/` → `lobby_pending` legend visible → attempt another route by URL → redirected back to `/`.
- As an `admins` member, grant a role to that user in `/admin/` → the pending user refreshes any page → the previously blocked route now renders normally, no re-login.
- Sign in as a user who already holds a role → `/` renders the normal session-badge content, no legend → every route opens per its own permission class.
- Until a project's shadow-test runner exists, this entry may reach `building`, never `shipped` ([[BDD]]).