---
title: tdd-06-router-starter-menu
type: tdd
status: green
created: 2026-08-04
api: []
tags: [tdd, router, chatui, seed]
---

# tdd-06 — the router starter menu and its seed command

## Context

Closes #135. The chatui surface is wired end to end — `POST /api/router/route/`, real Bedrock inference ([[tdd-03-router-bedrock-inference]]), the RBAC gate — but the hand-authored `Intent` registry is **empty** in local and in prod. `build_menu` on an empty registry returns nothing but the two reserved outcomes ([[adr-15-chatbot-two-tier]] rule 2), so the choosing tier can only ever answer `NO_MATCH` or `ESCALATE`: the drawer is alive and mute. What is missing is not code, it is registry rows.

This entry is the **management command that seeds them**, a single coherent piece ([[TDD]] — one entry, one coherent piece). It adds no route and changes no row of [[API]] (`api: []`): the starter menu enters through `Intent`, the existing registry model, and is read by the existing `POST /api/router/route/` handler. There is no free-text generation anywhere in it — every phrase and target is hand-authored here, which is exactly what [[adr-15-chatbot-two-tier]] rules 2 and 5 demand of a menu member.

## Design

- **`STARTER_MENU`** ([[GLOSSARY]]: *router starter menu*) — a module-level tuple of 13 rows in `backend/apps/router/management/commands/seed_router_menu.py`, each `(phrase, target, kind, group_name, order)`: the profile, the eleven feedlot destinations, and logout as a `confirm`. It is **product registry, not demo data** — no client, herd or account identifier appears in it ([[PRD]] — agnostic to company, farm and account). Phrases are the user-facing Spanish the drawer renders; the code around them is English ([[LOCALIZATION]] — other languages exist only in rendered frontend output, and a registry phrase *is* rendered output).
- **The gate on every row is `field_managers`, with exactly one ungated exception: `Cerrar sesión`.** This is not a style choice, it is [[adr-20-authorization-lobby]] rule 1: a role-less authenticated session is confined to the lobby, and the only routes standing outside that gate are `/accounts/*` and the health routes. `/accounts/logout/` is an `/accounts/*` route, so it is the one destination a role-less session may legitimately be offered — offering it `/profile/` or `/feedlot/` would be the "second door" rule 2 forbids. Gating is enforced where it already lives, in `build_menu`'s permission filter; the seed only authors the `group` FK it reads.
- **`seed_router_menu`** ([[GLOSSARY]]: *router starter menu seed command*) — idempotent upsert, one `update_or_create` per row keyed on `phrase` (the model's unique column). The split between the two defaults dicts is the whole design:
  - `create_defaults` carries `is_active=True` — a **new** row arrives active, otherwise the seed would be decorative.
  - `defaults` deliberately **omits `is_active`** and carries `target`/`kind`/`group`/`order`. So a re-run repairs drift in where a phrase points and who may see it (the fields the product owns), and never resurrects a row an operator switched off in `/admin/` (the field the operator owns). An idempotent seed that silently re-enables a deliberately disabled menu row would be a seed that overrules its operator.
- **`full_clean(validate_unique=False)` on a candidate instance before every write.** The `path_relative_validator` on `Intent.target` (no absolute URLs, #107) and the reserved-outcome `CheckConstraint` are both real gates, and `update_or_create` runs neither. Validating first means a bad starter row fails in the command, loudly, instead of landing in the registry. `validate_unique=False` is what keeps the *second* run from tripping the unique `phrase` it is about to update.
- **`Group.objects.get_or_create(name=…)`** for the gate: the command must be runnable on any database, and it never assumes migration `users.0007` has already provisioned the role groups.
- **No DEBUG gate** ([[adr-10-auth]] rule 6 is deliberately *not* invoked here). The mock-inference and dev-login precedents gate a *development shortcut*; this is the product's real menu, and prod needs it as much as local does — issue #135 acceptance, "usable outside DEBUG so prod can get the same starter menu". Contrast the DEBUG-only demo feedlot data, which stays demo data.
- **`backend/apps/router/fixtures/intents.json` is deleted.** It held two placeholder rows (`log me out`, `go to the dashboard` → `/dashboard/`, a path this project has no route for) and nothing loaded it — no `loaddata` call, no test, no boot step. Keeping a second, dead, un-run source of registry truth beside the live one is the duplication the one-SSOT-per-topic meta-rule ([[AGENTS]]) exists to prevent: `STARTER_MENU` is now that single source.

## Tests (`backend/apps/router/test_seed_router_menu.py`)

`pytest.mark.django_db` + `call_command`, following `test_purge_router_audit.py`. The gating tests assert through `build_menu`, not by re-reading the queryset, because `build_menu` is what the router actually offers the model.

1. `test_seed_creates_every_starter_row` — a fresh registry gets exactly 13 active `Intent` rows, phrases and targets equal to `STARTER_MENU`.
2. `test_seed_is_idempotent` — a second run creates no duplicate phrase and leaves the count at 13.
3. `test_seed_repairs_drifted_row` — a row hand-edited to a wrong `target`/`kind`/`order` and a wrong `group` is restored by the next run (the `defaults` half).
4. `test_deactivated_row_stays_deactivated` — a row an operator set `is_active=False` on is **not** re-enabled by a re-run (`is_active` absent from `defaults`).
5. `test_owner_authored_row_survives_the_seed` — an `Intent` outside `STARTER_MENU` is neither deleted nor modified; the seed upserts, it does not synchronise.
6. `test_every_target_is_path_relative_and_no_phrase_is_reserved` — every seeded `target` passes `path_relative_validator` and no `phrase` equals `NO_MATCH`/`ESCALATE`, so no starter row can point off-site or collide with a reserved outcome.
7. `test_role_less_session_is_offered_only_logout` — [[adr-20-authorization-lobby]] rules 1–2 as a test: a group-less session's menu is exactly `Cerrar sesión` + `NO_MATCH` + `ESCALATE`; `Ir al perfil` and `Abrir clientes` are **absent**.
8. `test_field_managers_session_is_offered_every_row` — a `field_managers` session sees all 13 registry rows plus the two reserved outcomes.
9. `test_lot_owners_session_is_offered_only_logout` — the boarding client's portal role reaches no starter destination but logout.
10. `test_feed_operators_session_is_offered_only_logout` — same for the mixer operative: a gate this seed did not grant is a gate that stays shut.
11. `test_seed_runs_outside_debug` — with `DEBUG=False` the command still seeds all 13 rows; there is no DEBUG gate to trip.

## Status

`draft → red → green` in one batch (#135): the eleven tests were written first against a repo with no `seed_router_menu` module (red: `ModuleNotFoundError` on the `STARTER_MENU` import, no command to `call_command`) and turned green by the command above, unchanged. `done` once the starter menu has been seeded on a real boot of the stack.
