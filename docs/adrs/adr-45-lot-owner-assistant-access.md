---
title: adr-45-lot-owner-assistant-access
type: adr
category: backend
use_case: open the conversational assistant to the client portal, gate /api/conversations/, verify per-client confinement of a lot_owners session
created: 2026-07-28
modified: 2026-08-04
tags: [adr, rbac, assistant, tenant-isolation, lot-owners, feedlot]
---

# ADR-45 — The lot-owner portal reaches the conversational assistant, scoped to its client

## CONTEXT

> The lot owner asks in natural language about their own livestock and balance. It is the same read the portal already authorizes over its metrics, served conversationally, and that is why it is enumerated as a third surface instead of widening the portal.

## ASSERTIONS

1. A `lot_owners` session reaches `GET`/`POST` on `/api/conversations/…` ([[adr-35-conversational-assistant]]) only for the client linked to its `AccessRequest`. The list that [[adr-44-field-operational-roles]] rule 3 enumerates becomes three: metrics, account, and assistant. No other route is opened.
2. `AssistantAccess` applies the same per-client barrier as `ClientScopedReadPermission`, through three paths: on list and create the requested `client` must equal the linked one; `has_object_permission` re-checks the conversation's client on a detail route; and the queryset filters lists to the linked client. Without a linked client, 403 — never "all clients".
3. The assistant remains read-only on the domain: it generates prose and does not execute actions, post entries, or change state ([[adr-35-conversational-assistant]] rule 1). A `lot_owners` creating a turn does not violate its read-only nature: the `POST` records its own question on its own conversation and triggers a generative read on its own snapshot.
4. Who reaches the assistant is decided by reading Django Groups in the backend, per request and with no cache in the path ([[adr-10-auth]] rule 2, [[adr-20-authorization-lobby]] rule 4). The frontend gates navigation for convenience; the barrier is the backend. The user→client link is set by an admin, never self-service.
5. Staff-only surfaces do not change: the client roster and one-shot generative reports remain closed to `lot_owners`. There is no new model, migration, or variable: this is an authorization rule on already-declared routes, and the class lives in `apps/users/roles.py` ([[adr-44-field-operational-roles]] rule 1).

## FORBIDDEN

- **NEVER** expand the portal without enumerating the route in an ADR (rule 1). A portal with a diffuse scope is exactly what [[adr-44-field-operational-roles]] rule 3 closed with the word "exactly".
- **NEVER** implement a per-client barrier parallel to the portal's (rule 2). Two mechanisms fall out of sync and leave two definitions of "my client".
- **NEVER** let a session without a linked client through (rule 2). Fails closed, always.
- **NEVER** give the assistant an actuator right to serve the portal (rule 3). The disjunction between choosing and generating is permanent.
- **NEVER** trust the frontend gate (rule 4). It is UX; the tenant boundary lives in Django.

## REJECTED

- **Opening the assistant to `lot_owners` without an ADR** — treating it as an already-authorized read and adding the route. Rejected: [[adr-44-field-operational-roles]] rule 3 requires the vehicle, and without it the enumerated list ceases to be enumerated.
- **Denying the portal access to the assistant** — keeping it staff-only because it is generative. Rejected as arbitrary: it sees no data beyond what the per-client snapshot already assembles for the metrics the portal reads.
- **A standalone `ClientScopedAssistantPermission`, written separately** — a twin class with its own logic. Lost against rule 2: reusing the portal's exact mechanism is what prevents the two surfaces from diverging.

## RELATED

### related adrs

- [[docs/adrs/adr-44-field-operational-roles]] — rules 1 and 3, the matrix and the list of routes this expands
- [[docs/adrs/adr-35-conversational-assistant]] — the conversational assistant and its read-only nature
- [[docs/adrs/adr-27-advisors-generative]] — rule 2, the per-client barrier that is reused
- [[docs/adrs/adr-15-chatbot-two-tier]] — rule 1, the permanent disjunction between choosing and generating
- [[docs/adrs/adr-20-authorization-lobby]] — rule 4, the per-request decision without cache

### related files

- [[docs/API]] — the `/api/conversations/…` rows and their auth cell
- [[docs/AUTH]] — the session and groups mechanism
