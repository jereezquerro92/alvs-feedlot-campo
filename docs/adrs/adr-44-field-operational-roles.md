---
title: adr-44-field-operational-roles
type: adr
category: backend
use_case: gate an endpoint by role, edit the permission matrix, link a user to their client, open a route to the lot-owner portal
created: 2026-07-27
modified: 2026-08-04
tags: [adr, rbac, auth, roles, feedlot]
---

# ADR-44 — The six field operational roles and per-client scoping

## CONTEXT

> Six real field roles, each with its own slice of what it sees and what it writes. One of them — the lot owner — is a client portal: it sees ONE client and no other, and that slice is a tenant-isolation boundary, decided and enforced in the backend.

## ASSERTIONS

1. The six roles are Django groups created by migration: `field_managers`, `feed_operators`, `lot_owners`, `field_admins`, `feedlot_owners` and `workshop`. `admins` retains the superset and `ai_operators` remains router-only. Authorization is decided by Group membership, read in Django and never from a Cognito claim ([[adr-10-auth]] rule 2); their names enter [[GLOSSARY]] before first use. The entire role → area → method matrix lives centralized in `apps/users/roles.py` (`GroupMatrixPermission`, with `read_groups` and `write_groups` per functional area): a viewset only references its area class, and adjusting who can do what means editing that single file.
2. `GroupMatrixPermission` accepts safe methods if the user is in `read_groups` and write methods if in `write_groups`; `admins` always passes. A role can read an area without being able to write it.
3. `lot_owners` is read-only and its scope is exactly the client-keyed routes enumerated by this rule and [[adr-45-lot-owner-assistant-access]] rule 1: metrics, the client account, and the conversational assistant. `ClientScopedReadPermission` compares the `client_id` in the route against the client linked to the session and rejects on mismatch. No raw domain table is exposed to them.
4. The user→client link is a nullable FK `client` on `AccessRequest`, set by an admin in `/admin/` ([[adr-20-authorization-lobby]] rule 3), never self-service. A `lot_owners` with no linked client sees no client — fails closed — never all of them. The field does not grant authority: group membership activates scoping and `client` only says which one.
5. `feedlot_owners`, `field_managers` and `admins` read without per-client scoping: they are internal feedlot roles, not tenants. The scoping of rule 3 applies only to `lot_owners`.
6. There is no manual-debit endpoint: "loading debts" is fulfilled by the events that already post and by `Payment`, all writable by `field_managers`. A manual adjustment, if the business requires it, enters through [[API]] with its own change and never by mutating an entry ([[adr-25-account-ledger]] rule 1).
7. Every endpoint declares its permission class in [[API]] before the code ([[adr-51-api-and-backend]] rule 1): the Auth column names the class, and therefore the groups, that protect the route.
8. `/api/me/` exposes the linked client so the frontend can trim the UI. That gate is convenience; the barrier is the backend.

## FORBIDDEN

- **NEVER** let a `lot_owners` reach a route outside the enumerated list (rule 3). The portal is a tenant boundary, and expanding it requires an ADR, never a local exception.
- **NEVER** give default access to a `lot_owners` with no linked client (rule 4). Fails closed; the opposite exposes all clients through an empty field.
- **NEVER** scatter the permission matrix across viewsets (rule 1). Spread across fifty files it falls out of sync and ceases to be auditable.
- **NEVER** decide a permission in the frontend (rule 8). Navigation gating is UX; the barrier lives in Django.
- **NEVER** open a manual-debit endpoint (rule 6). The ledger is immutable and convenience does not justify opening a direct write to an entry.

## REJECTED

- **Isolating `lot_owners` by queryset in each model** — filtering ~15 models by their path to the client. Rejected by surface area: a single error in one path leaks another tenant's data. Confining the portal to routes already keyed by `client_id` reduces everything to a single testable comparison.
- **Letting the user choose their client** — the link declared by whoever requests access. Rejected by rule 4: it is the same self-service door that [[adr-20-authorization-lobby]] rule 3 closed.
- **One permission class per role/area/method combination** — bespoke permissions per endpoint. Lost against rules 1 and 2: the matrix with `read_groups`/`write_groups` covers the requirement without multiplying classes.

## RELATED

### related adrs

- [[docs/adrs/adr-20-authorization-lobby]] — rules 2 and 3, session scope and how a role is granted
- [[docs/adrs/adr-10-auth]] — rules 1–2, Cognito authenticates and Django authorizes
- [[docs/adrs/adr-45-lot-owner-assistant-access]] — the third route the portal reaches
- [[docs/adrs/adr-25-account-ledger]] — rule 1, why there is no manual debit
- [[docs/adrs/adr-51-api-and-backend]] — rule 1, the gate declared in [[API]] before the code

### related files

- [[docs/API]] — the Auth column of each route
- [[docs/AUTH]] — the session on which the role is decided
- [[docs/GLOSSARY]] — the names of the six groups
- [[docs/feedlot/09-usuarios-y-permisos]] — the field functions these roles model
