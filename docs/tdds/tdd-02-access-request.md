---
api: []
created: '2026-07-14'
status: green
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

Backend half of the authorization-lobby feature: the model and signal that back [[adr-20-authorization-lobby]]'s gate — every route requires an authenticated session AND at least one Django Group, except the lobby `/`. This entry is `AccessRequest` ([[GLOSSARY]]), its nullable `role` field ([[GLOSSARY]]), and the `post_save` signal that mirrors a granted `role` into `user.groups`. **`api: []`** — no [[API]] row exists for this entry: the admin grant path reuses the already-declared `/admin/` mount, and the frontend reads the resulting authorization state through the already-declared `GET /api/me/` `groups` field ([[API]]). No row is added or widened here.

## Design

- **Placement:** the `users` app ([[GLOSSARY]]: Django app (users)) — `AccessRequest` is identity/authorization-adjacent to the `sub`-keyed user model already owned there; [[BACKEND]]'s one-app-per-domain rule does not warrant a new app for a single admin-managed model.
- **Model:** `AccessRequest` — a `OneToOneField` to `User` (`on_delete=CASCADE`, `related_name="access_request"`; one row per user, created alongside the user row in the same `get_or_create` login path [[AUTH]] already runs at real callback and dev-login), plus `role` — `ForeignKey("auth.Group", null=True, blank=True, on_delete=models.SET_NULL)` — `null` is the pending/unassigned state ([[adr-20-authorization-lobby]] rule 1). A `created_at` timestamp (`auto_now_add=True`) records when the request first existed.
- **Signal:** a `post_save` receiver on `AccessRequest` (`sync_role_group_membership`) that **set-syncs** matrix membership: removes every `ROLE_GROUPS` ([[adr-44-field-operational-roles]]) membership that is not the current `role`, then — when `role` is non-null — adds that Group. Clearing `role` to `null` strips all `ROLE_GROUPS` memberships. Out-of-matrix Groups (`admins`, `ai_operators`) are never touched by this sync — hand-granted or previously mirrored memberships outside `ROLE_GROUPS` stay. This is the sole path from the row to matrix authority ([[adr-20-authorization-lobby]] rule 3); the row itself is inert until the signal runs.
- **Gate:** a session-scoped check — applied to every route except `/` and the routes already carrying `none`/`AllowAny` auth in [[API]] (`/accounts/*`, `/api/health/`, `/api/m365/hello/`, `/api/m365/world/`) — that redirects a session with `request.user.groups.exists() is False` back to `/`, never a `403` ([[adr-20-authorization-lobby]] rule 2). This entry does not touch any [[API]] row's Auth column; the check is orthogonal to, and runs alongside, each route's own permission class.
- **No cache layer, no new variable:** Group membership is read fresh every request straight off the session-backed `request.user` — nothing sits between a grant and its enforcement ([[adr-06-cache]]); no [[VARIABLES]] row is needed.
- **Boundaries:** clearing `AccessRequest.role` to `null` is durable only when the user's email is **not** on [[adr-21-bootstrap-allowlist-grant]]'s allowlist — an allowlisted email is re-filled (and the Group restored by this signal) on the next login. A hand-edit of Groups outside `ROLE_GROUPS` is durable across role demote/clear; a hand-edit *inside* `ROLE_GROUPS` is non-durable — the next `AccessRequest` save re-asserts the set-sync.

## Tests (`backend/apps/users/test_access_request.py`)

- `test_first_login_creates_exactly_one_access_request`
- `test_access_request_role_is_null_by_default`
- `test_second_login_creates_no_duplicate`
- `test_setting_role_adds_group_to_user`
- `test_resave_same_role_is_idempotent`
- `test_resave_null_role_does_not_error`
- `test_admin_role_editable_while_pending`
- `test_admin_role_stays_editable_after_grant`
- `test_admin_role_help_text_documents_set_sync_contract`
- `test_reassign_between_out_of_matrix_roles_keeps_both`
- `test_clearing_role_keeps_out_of_matrix_group`
- `test_demoted_user_loses_staff_directory_access`
- `test_reassign_role_strips_previous_role_group`
- `test_clearing_role_strips_all_role_groups`
- `test_sync_preserves_hand_granted_admins`
- `test_sync_preserves_ai_operators_when_role_cleared`
- `test_resave_same_role_does_not_thrash_role_group`
- `test_me_endpoint_does_not_leak_access_request`

Allowlist companion (`backend/apps/users/test_bootstrap_allowlist.py`):

- `test_allowlist_refills_cleared_role_and_restores_group_on_next_login`
- `test_cleared_role_stays_revoked_when_email_not_allowlisted`

## Status

`green`. Set-sync is implemented: `sync_role_group_membership` strips stale `ROLE_GROUPS` on demote/clear, preserves out-of-matrix Groups, admin `role` stays editable with set-sync help text, and allowlist re-fill after a clear is documented and covered.
