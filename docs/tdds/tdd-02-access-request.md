---
api: []
created: '2026-07-14'
status: draft
tags:
- tdd
- users
- auth
- lobby
- rbac
title: tdd-02-access-request
type: tdd
---

# tdd-02 — access request

## Context

Backend half of [[bdd-08-authorization-lobby]]: the model and signal that back [[adr-20-authorization-lobby]]'s gate — every route requires an authenticated session AND at least one Django Group, except the lobby `/`. This entry is `AccessRequest` ([[GLOSSARY]]), its nullable `role` field ([[GLOSSARY]]), and the `post_save` signal that mirrors a granted `role` into `user.groups`. **`api: []`** — no [[API]] row exists for this entry: the admin grant path reuses the already-declared `/admin/` mount, and the frontend reads the resulting authorization state through the already-declared `GET /api/me/` `groups` field ([[API]]). No row is added or widened here.

## Design

- **Placement:** the `users` app ([[GLOSSARY]]: Django app (users)) — `AccessRequest` is identity/authorization-adjacent to the `sub`-keyed user model already owned there; [[BACKEND]]'s one-app-per-domain rule does not warrant a new app for a single admin-managed model.
- **Model:** `AccessRequest` — a `OneToOneField` to `User` (`on_delete=CASCADE`, `related_name="access_request"`; one row per user, created alongside the user row in the same `get_or_create` login path [[AUTH]] already runs at real callback and dev-login), plus `role` — `ForeignKey("auth.Group", null=True, blank=True, on_delete=models.SET_NULL)` — `null` is the pending/unassigned state ([[adr-20-authorization-lobby]] rule 1). A `created_at` timestamp (`auto_now_add=True`) records when the request first existed.
- **Signal:** a `post_save` receiver on `AccessRequest` that, only when `role` is non-null, calls `instance.user.groups.add(instance.role)` — additive, never removing an existing Group the user already holds. This is the sole path from the row to actual authority ([[adr-20-authorization-lobby]] rule 3); the row itself is inert until the signal runs.
- **Gate:** a session-scoped check — applied to every route except `/` and the routes already carrying `none`/`AllowAny` auth in [[API]] (`/accounts/*`, `/api/health/`, `/api/m365/hello/`, `/api/m365/world/`) — that redirects a session with `request.user.groups.exists() is False` back to `/`, never a `403` ([[adr-20-authorization-lobby]] rule 2, [[bdd-08-authorization-lobby]] — Error handling). This entry does not touch any [[API]] row's Auth column; the check is orthogonal to, and runs alongside, each route's own permission class.
- **No cache layer, no new variable:** Group membership is read fresh every request straight off the session-backed `request.user` — nothing sits between a grant and its enforcement ([[adr-06-cache]]); no [[VARIABLES]] row is needed.

## Tests (`backend/apps/users/test_access_request.py`)

- `test_access_request_created_with_role_none_on_first_login` (real callback and dev-login paths, parametrized)
- `test_lobby_route_allows_anonymous_visitor`
- `test_lobby_route_allows_role_less_authenticated_session_and_shows_pending_state`
- `test_non_lobby_route_redirects_anonymous_visitor_to_login`
- `test_non_lobby_route_redirects_role_less_session_to_lobby_not_403`
- `test_admin_sets_role_mirrors_into_user_groups_via_signal`
- `test_role_takes_effect_on_next_request_no_relogin_required`
- `test_signal_is_additive_does_not_remove_existing_group_membership`
- `test_role_holding_user_reaches_every_route_unaffected_by_this_gate`
- `test_lobby_gate_does_not_alter_existing_allowany_routes` (`/accounts/*`, `/api/health/`, `/api/m365/hello/`, `/api/m365/world/` stay reachable role-less)
- `test_get_me_groups_field_reflects_granted_role` (regression on the existing `GET /api/me/` contract, [[API]])

## Status

`draft`. No test has been written yet; this entry is the gate that authorizes the [[TDD]] flow to start — tests are written first, against a pre-migration model, and confirmed red before `AccessRequest` (model, migration, signal, gate) is implemented.