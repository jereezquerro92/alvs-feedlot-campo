---
title: adr-45-lot-owner-assistant-access
type: adr
status: active
created: 2026-07-28
tags: [adr, rbac, assistant, tenant-isolation, lot-owners, feedlot, phase-module-first-redesign]
---

# ADR-45 — the lot owner's portal reaches the conversational assistant, bounded to their client

**Context:** widens [[adr-44-field-operational-roles]] decision 3 (which routes a `lot_owners`
session reaches) through the path that same decision requires — a new ADR, never a local
exception ([[adr-20-authorization-lobby]] rule 2, the precedent of the bounded exceptions of
[[adr-13-m365-graph]] rule 3). Reuses the read-only per-client barrier of
[[adr-27-advisors-generative]] rule 2 and the permanent generate/choose disjunction of
[[adr-15-chatbot-two-tier]] rule 1. Rules only; the mechanism lives in [[AUTH]], the matrix in
`apps/users/roles.py` and the route contract in [[API]].

## Context

[[adr-44-field-operational-roles]] decision 3 confined `lot_owners` (client portal, read-only)
to **exactly two** client-keyed surfaces: the metrics (`/api/metrics/{client_id}/…`) and the
account (`/api/clients/{id}/account|ledger|outstanding`), both gated by
`ClientScopedReadPermission`. The module-first redesign adds the **conversational assistant**
(`assistant`, [[adr-35-conversational-assistant]]) as a portal module: the lot owner asks in
natural language about **their own** cattle and their balance, and gets a grounded answer.

That read is exactly the one `lot_owners` already has authorized over their metrics — the
assistant sees not one datum more than the per-client snapshot already assembles
([[adr-27-advisors-generative]] rule 2). But it is a **third** reachable route, and
[[adr-44-field-operational-roles]] fixed its list with the word "exactly" and mandated that
widening it requires an ADR (decision 3 and the final consequence, rules 1–7 semantic). This ADR
is that vehicle. It does not touch adr-44's body; it widens it by addition.

## Decisions

### 1. The assistant is a third surface reachable by `lot_owners`, bounded to their client

A `lot_owners` session reaches `GET/POST /api/conversations/…`
([[adr-35-conversational-assistant]], [[API]]) **only** for the client bound to their
`AccessRequest` ([[adr-44-field-operational-roles]] decision 4). The per-client route list that
adr-44's decision 3 declared "exactly" becomes **three**: metrics, account and **assistant**. No
other route is opened; this widening is additive and enumerated, not a general broadening of the
portal.

*Why:* asking the assistant about one's own cattle is the same read the portal already
authorizes over the metrics, served conversationally. Denying it would be arbitrary; opening it
without enumerating it would reopen the door to a portal of diffuse scope that adr-44 decision 3
closed on purpose.

### 2. The confinement is identical to the portal's and fails closed

`AssistantAccess` applies the same per-client barrier as `ClientScopedReadPermission`, through
the three routes keyed on the bound client ([[adr-44-field-operational-roles]] decision 4): on
list/create the requested `client` (query param or body) must equal the bound one;
`has_object_permission` re-verifies the conversation's client on a detail route; and the
viewset's queryset filters the lists to the bound client. A `lot_owners` session with no bound
client reaches **nothing** — 403, never "all clients".

*Why:* a tenant boundary is defined once and enforced identically at every door. Reusing the
portal's exact mechanism (not a parallel one) keeps the two surfaces from drifting apart and
leaves a single definition of "my client".

### 3. The assistant stays read-only over the domain; asking is not acting

The assistant generates analytical prose and **never** executes an action, posts an entry or
changes domain state ([[adr-35-conversational-assistant]] decision 1,
[[adr-15-chatbot-two-tier]] rule 1). That a `lot_owners` can **write** a turn (`POST`) does not
violate the portal's read-only nature: the POST creates a message on their own conversation and
triggers a generative read over their own snapshot — it mutates not one domain record of the
client. Adr-15's permanent choose/generate disjunction stays intact: the assistant is not the
router and gains no actuator rights.

*Why:* adr-44's read-only rule protects the tenant's **domain data**; it does not forbid
recording the tenant's own question. The turn is an auditable record
([[adr-35-conversational-assistant]] decision 4), not a domain write.

### 4. Authorization in Django, by Group, per request

Who reaches the assistant is decided by reading Django Groups in the backend, per request, with
no cache in the path ([[adr-10-auth]] rule 2, [[adr-20-authorization-lobby]] rule 4). The
frontend gates navigation to the module for UX convenience; the barrier is the backend. The
user→client link is set by an admin in `/admin/`, never self-service
([[adr-44-field-operational-roles]] decision 4).

*Why:* the same doctrine as all the system's RBAC. The portal is a security boundary and lives
where the authority lives, in Django.

## Consequences

- The backend enters only through [[API]] ([[adr-03-api-and-backend]]): the `/api/conversations/…`
  rows name `AssistantAccess` and their auth cell documents the `lot_owners` confinement. The
  class lives in `apps/users/roles.py`, the matrix's single home
  ([[adr-44-field-operational-roles]] decision 1).
- There is no new model, migration or environment variable: this is an authorization rule over
  already-declared routes ([[adr-35-conversational-assistant]]).
- The staff-only surfaces do not change: the client roster (`ClientDirectoryAccess`) and the
  one-shot generative advisor reports (`AdvisorAccess`) stay closed to `lot_owners` — this ADR
  opens the per-client conversational assistant and nothing else.
- Cognito still authenticates only and RBAC remains exclusively Django Groups ([[adr-10-auth]]
  rules 1–2, intact); [[adr-44-field-operational-roles]]'s body is not edited.
- Any change to rules 1–4 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
