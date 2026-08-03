---
title: adr-44-field-operational-roles
type: adr
status: active
created: 2026-07-27
tags: [adr, rbac, auth, roles, feedlot, phase-users]
---

# ADR-44 — the six field operational roles and per-client scoping

**Context:** widens [[adr-20-authorization-lobby]] rule 2 (adding a role scope or widening which
routes a session reaches requires a new ADR, never a local exception) and reuses the
group-per-concern precedent of [[adr-11-guardians]] and the `AccessRequest` + `post_save` signal
pair of [[adr-20-authorization-lobby]] rule 3. It supersedes nothing: Cognito still
authenticates and Django Groups remain the sole RBAC authority ([[adr-10-auth]] rules 1–2,
intact). Rules only; the names enter [[GLOSSARY]] before their first use
([[adr-01-glossary-and-localization]]).

## Context

The template left two groups: `admins` (superset) and `ai_operators` (router only). The owner
asked for the real field roles: six distinct functions, each with its own cut of what it can see
and load. One of them — the lot owners — is a **client portal**: it sees ONE client's data and
nobody else's. That cut is a tenant isolation boundary, not a UI convenience, and that is why it
is decided and enforced in the backend.

## The six roles (Django groups)

| Role (business) | Django group | Nature |
|---|---|---|
| Field manager | `field_managers` | staff; sees everything operational; loads debts (accounts) |
| Feed operator (mixer) | `feed_operators` | staff; prepares the mixer (loading orders, feeding, bunk reading) |
| Lot owners | `lot_owners` | client portal; **read-only**; bounded to THEIR client |
| Field administrative | `field_admins` | staff; loads goods receipts into stocks (field and own-by-contract) |
| Feedlot owner | `feedlot_owners` | staff/owner; **read** across all clients (cattle by contract and own) |
| Workshop users | `workshop` | staff; loads machinery, maintenance, fuel, alfalfa (crops) |

`admins` keeps the superset: it can do everything and is accepted by every permission class
(short-circuited in the base class). `ai_operators` remains router-only and is added to no other
class ([[adr-11-guardians]], [[GLOSSARY]]).

## Decisions

### 1. A role is a Django Group; the matrix lives in a single file

Each role is an `auth.Group` created by migration (the same pattern as `admins`,
[[adr-10-auth]]). Authorization is decided by Group membership, read in Django, never from a
Cognito claim ([[adr-10-auth]] rule 2). The whole role→area→method matrix lives centralized in
`apps/users/roles.py` (`GroupMatrixPermission` with `read_groups` / `write_groups` per
functional area); a viewset only references its area class. Adjusting who can do what is editing
that single file, not hunting permissions across every app.

*Why:* a matrix scattered across 50 viewsets drifts out of sync. Centralizing it makes it
auditable at a glance and cheap to correct when the owner tunes it.

### 2. `read`/`write` are separated by HTTP method within each area

`GroupMatrixPermission` accepts safe methods (GET/HEAD/OPTIONS) if the user is in `read_groups`
and write methods (POST/PUT/PATCH/DELETE) if they are in `write_groups`. `admins` always passes.
A role can read an area without being able to write it (e.g. the feedlot owner reads stocks but
does not load them).

*Why:* almost every role is "see this, load that". Modelling read and write as separate sets per
area covers the request without a class per combination.

### 3. Lot owners are confined to a per-client surface, gated by the route's `client_id`

`lot_owners` is **read-only** and its scope is exactly the routes keyed by a client: the metrics
(`/api/metrics/{client_id}/…`) and the client's account
(`/api/clients/{id}/account|ledger|outstanding`). `ClientScopedReadPermission` compares the
route's `client_id`/`pk` against the client bound to the session (`AccessRequest.client`,
decision 4) and **rejects (404/403) on a mismatch**. The raw list of animals/feedings/etc. is not
exposed to them: they see **aggregated metrics of their cattle and their balance** — exactly what
was asked — and no table that could mix clients.

*Why:* isolating by queryset across ~15 models (each with its own path to the client) is where a
single mistake leaks another tenant's data. Confining the portal to the routes already keyed by
`client_id` reduces the surface to **one** comparison, testable and unambiguous. Zero exposure by
default is preferable to a broad, fragile filter.

### 4. The user→client link is a field on `AccessRequest`, set by an admin

`AccessRequest` gains a nullable `client` FK → `clients.Client`. An admin sets it in `/admin/`
(the same posture as [[adr-20-authorization-lobby]] rule 3: a grant is an admin action, never
self-service). A `lot_owners` with no linked `client` sees **no** client — it fails closed —
never "all by default". The field grants no authority by itself: membership in the `lot_owners`
group is what activates the scoping; `client` only says *which one*.

*Why:* it reuses the existing grant machinery and keeps the access decision in Django and in an
admin's hands. Failing closed on a missing link is the only safe option for a tenant boundary.

### 5. The feedlot owner and the field manager see all clients; they are not scoped

`feedlot_owners` and `field_managers` (and `admins`) read with no per-client cut: the feedlot
owner's request is to aggregate "how many animals I have, by contract and own", which is a
cross-client view. Decision 3's per-client scoping applies **only** to `lot_owners`.

*Why:* they are internal feedlot roles, not tenants. Cutting them by client would contradict
their function.

### 6. The manager's "loading debts" is events and payments, not a manual debit

The ledger is event-sourced and immutable ([[adr-25-account-ledger]] rule 1): there is no
"manual debit" endpoint. "Loading debts into current accounts" is served by what already posts to
the ledger — events that charge (feeding from own stock, sanitary) and `Payment` (credit) — all
writable by `field_managers`. A manual adjustment endpoint, if the business asks for it, enters
as its own change through [[API]] and [[adr-07-development-flow]], never by mutating an entry.

*Why:* we honour the ledger doctrine. The convenience of an arbitrary debit does not justify
opening a direct write to the entry that [[adr-25-account-ledger]] closed.

### 7. Every feedlot endpoint declares its permission class in [[API]] before the code

[[API]]'s Auth column stops saying a generic `session` for the gated routes: it states the
permission class (and therefore the groups) protecting them ([[adr-03-api-and-backend]] rule 1).
Changing a route's gating is changing its row first.

*Why:* [[API]] is the SSOT of the route contract; the gating is part of the contract.

## Consequences

- The backend enters only through [[API]] ([[adr-03-api-and-backend]]) and is born through the
  [[TDD]] flow ([[adr-07-development-flow]]); this ADR grants no exception to that path.
- Migrations: one creates the six groups; another adds `AccessRequest.client`. No domain model is
  refactored — the extraction looks forward ([[adr-32-multi-rubro-assets]] rule 2).
- `/api/me/` gains the linked client (id + name) so the frontend can scope the UI; the backend
  remains the security boundary, the frontend is only UX.
- The frontend gates navigation and routes by `me.groups` and uses `me.client` for the lot
  owner's portal; that gating is convenience, not the barrier (the barrier is the backend).
- Decision 1's matrix is a pre-v1 iteration surface: the owner tunes it by editing `roles.py` and
  this table; changes to rules 1–7 are semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
