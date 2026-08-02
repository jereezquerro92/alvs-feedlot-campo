---
title: adr-20-authorization-lobby
type: adr
category: backend
use_case: gating a route, granting a role, writing a permission class, touching AccessRequest or the landing page
created: 2026-07-14
modified: 2026-08-02
tags: [adr, auth, lobby, rbac, access-request]
---

# ADR-20 — the authorization lobby

## CONTEXT

> A session that Cognito authenticated but that carries no role reaches exactly one route: `/`, the lobby. A role arrives only by an admin's hand, through `AccessRequest` and the signal that mirrors it into Django Groups.

## ASSERTIONS

1. Every route requiring authentication requires an authenticated Django session AND membership in at least one Django Group, except `/`. A session with zero Group memberships is confined to the lobby ([[GLOSSARY]]) until that changes; RBAC stays Django Groups, decided in Django, never read from a Cognito claim ([[adr-10-auth]] rules 1–2). Routes declaring no authentication at all sit outside this gate rather than relaxing it — the `AllowAny` exception of [[adr-13-m365-graph]] rule 3, and the `/accounts/*` and health routes whose scope [[API]] owns.
2. `/` is the lobby: the sole route admitting both an anonymous visitor and a role-less authenticated session into the app's gated surface. Admitting a role-less user anywhere else widens this boundary and takes a new ADR.
3. A role grant is an admin action, never self-service. A member of `admins`, working in Django admin, sets the `role` field on the requesting user's `AccessRequest` row ([[GLOSSARY]]); a `post_save` signal mirrors a non-null `role` into the user's Django Groups. The Group membership is what rule 1 checks — `AccessRequest` is a record, not a permission, and carries no authority until the signal runs.
4. Re-evaluation is per-request, riding the existing Django session: no token re-mint and no cache in the path ([[adr-06-cache]]). A page refresh after a grant is enough for the new membership to take effect, read through the `/api/me/` `groups` field ([[API]]) and Django's own membership check.
5. Cognito remains authentication-only and RBAC remains exclusively Django Groups ([[adr-10-auth]] rules 1–2). This ADR narrows which routes a role-less session reaches and names the mechanism by which a role stops being role-less; it changes nothing else about auth.

## FORBIDDEN

- **NEVER** admit a role-less session to a route other than `/` (rule 2). That is the boundary the lobby exists to draw, and a second door is a widening, not an exception.
- **NEVER** read a role from a Cognito claim (rule 1). The Groups are the authority; a claim is an assertion by the IdP about a subject, not a grant by this project.
- **NEVER** treat an `AccessRequest` row as a permission (rule 3). Until the signal writes the Group, the row is a request that was recorded and nothing more.
- **NEVER** grant a role from user-facing code (rule 3). A grant is an admin act in `/admin/`; self-service would make the lobby decorative.
- **NEVER** cache an authorization decision (rule 4). A cached grant outlives its revocation.

## REJECTED

- **Self-service role selection** — a role chosen by the user on the request form and applied on save. Rejected outright: it would make every gate in the project advisory. The form records what is asked; an admin decides what is granted.
- **Checking `AccessRequest.role` directly in the permission classes** — skipping the Groups and reading the row. It looked simpler and lost because it would create a second authority alongside Django Groups, and the two disagree the moment an admin edits a Group by hand.

## RELATED

### related adrs

- [[docs/adrs/adr-10-auth]] — rules 1–2, Cognito authenticates and Django authorizes
- [[docs/adrs/adr-13-m365-graph]] — rule 3, the `AllowAny` routes outside this gate
- [[docs/adrs/adr-06-cache]] — why nothing caches between a grant and its enforcement
- [[docs/adrs/adr-44-field-operational-roles]] — the roles granted through this mechanism

### related files

- [[docs/AUTH]] — the login flow and the session it establishes
- [[docs/API]] — `/api/me/`, `/admin/` and the routes outside the gate
- [[docs/GLOSSARY]] — *lobby*, *role*, *AccessRequest*
