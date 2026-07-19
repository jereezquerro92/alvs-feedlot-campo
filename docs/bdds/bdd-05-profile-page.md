---
title: bdd-05-profile-page
type: bdd
status: draft
created: 2026-07-14
tags: [bdd, profile, users]
---

# bdd-05 — profile page

## Use case

As a logged-in user, when I open my profile page, I can (1) set or clear a
nickname shown instead of my Cognito-derived name, and (2) toggle whether my
avatar picture is visible — falling back to two-letter initials when hidden.
Both changes are confirmed and persisted through `PATCH /api/me/` ([[API]]).

## Frontend half

**Nickname edit — Svelte island, rung 3 of the interactivity ladder**
([[adr-04-frontend-and-design-system]] rule 3). A textbox plus an icon-only
confirm button, guarded by a reusable `ConfirmDialog.svelte` wrapping
shadcn-svelte's `AlertDialog` (accept/cancel; escape/backdrop behaves as
cancel). The draft text, dirty flag, and the confirm modal's open/closed state
are client-owned transient state that only resolves into a server write on
explicit accept — HTMX (rung 2) would need a fragment round-trip per
keystroke-adjacent interaction for a two-control widget, with no server-owned
state to render until submit, so escalating past HTMX to a Svelte island is
justified, not a rung skip.

**Avatar visibility — same single Svelte island, not a separate HTMX
fragment.** A dedicated HTMX fragment route for one boolean toggle would need
its own [[API]] row per [[adr-05-htmx]] rule 3 ("no shadow routes"), and
this feature is scoped YAGNI-minimal — no new route beyond the existing
`PATCH /api/me/`. Both controls are therefore
delivered as one island so the toggle can call the same `PATCH /api/me/`
client-side that the nickname confirm already calls, with no additional
backend surface. This is the interactivity-ladder decision owed by
[[adr-07-development-flow]] rule 1, recorded here per
[[adr-04-frontend-and-design-system]] rule 3.

Design system: per [[DESIGN-SYSTEM]]. `Avatar` /
`AvatarImage` / `AvatarFallback` render the picture when `avatar_visible` is
true, else two-letter initials derived from `nickname` if set, else
`given_name`+`family_name`. Variables consumed: none beyond existing
session-scoped fetches — no `PUBLIC_*` addition ([[VARIABLES]]).

## Backend half

Reuses the existing `PATCH /api/me/` row ([[API]]) — no new endpoint. Feeds
the TDD entry owed for `PATCH /api/me/`: partial update of `nickname` and
`avatar_visible`, read-only-field rejection, blank-nickname fallback
behavior, `no-store` header, `403` without session.

## Error handling

A `400` from `PATCH /api/me/` (read-only field mismatch or unexpected key)
surfaces inline next to the offending control — the confirm dialog stays
open on nickname failure; the toggle reverts to its prior state on avatar
failure. `403` (session expired mid-edit) redirects to `/accounts/login/`.
All responses `no-store` ([[CACHE]] rule 4).

## Shadow-test spec

- Open profile page → nickname textbox shows current value (empty when
  unset) → type a new value → click confirm icon → `ConfirmDialog` opens →
  accept → `PATCH /api/me/` fires → displayed name updates to the nickname.
- Same flow, cancel in the dialog → no request fires, textbox retains the
  draft, displayed name unchanged.
- Toggle avatar visibility off → picture replaced by two-letter initials →
  toggle on → picture restored.
- Until a project's shadow-test runner exists, this entry may reach
  `building`, never `shipped` ([[BDD]]).
