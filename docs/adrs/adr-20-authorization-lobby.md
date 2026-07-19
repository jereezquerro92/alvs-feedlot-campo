---
title: adr-20-authorization-lobby
type: adr
status: active
created: 2026-07-14
tags: [adr, auth, lobby, rbac, access-request]
---

# ADR-20 — the authorization lobby

Rules only; content lives in [[AUTH]], [[GLOSSARY]], [[API]]. This ADR adds to [[adr-10-auth]]; it narrows nothing that ADR states and is not a supersession.

1. Every route requiring authentication requires an authenticated Django session AND membership in at least one Django Group, except `/`. A session authenticated by Cognito but carrying zero Group memberships is confined to `/` ([[GLOSSARY]]: lobby) until that changes — RBAC stays Django Groups, decided in Django, never a Cognito claim ([[adr-10-auth]] rules 1–2). Routes that already declare no authentication at all are outside this gate, not relaxations of it: the `AllowAny` named exception of [[adr-13-m365-graph]] rule 3 and the pre-existing `/accounts/*` and health routes, whose scope is owned by [[API]] and the gate list in [[tdd-02-access-request]].

2. `/` is the lobby — the sole route that admits both an anonymous visitor and a role-less authenticated session into the app's gated surface. No other route may ever relax rule 1 to admit a role-less user; a second such route is a widening of this boundary and requires a new ADR, never a local exception. The one standing exception is the bounded `AllowAny` carve-out of [[adr-13-m365-graph]] rule 3 — owner-directed and predating this ADR — which admits anonymous requests to two demo routes and is neither widened nor reopened here.

3. A role grant is an admin action, never self-service. A member of the `admins` role, working in Django admin (the existing `/admin/` mount, [[API]]), sets the `role` field ([[GLOSSARY]]) on the requesting user's `AccessRequest` row ([[GLOSSARY]]). A `post_save` signal on that write mirrors the non-null `role` into the user's Django Groups — the Group membership is what rule 1 checks, never the `AccessRequest` row itself. `AccessRequest` carries no authority until the signal runs; it is a record, not a permission.

4. Re-evaluation is per-request, riding the existing Django session — no token re-mint, no cache in the path. A page refresh after a grant is sufficient for the new Group membership to take effect on the next request, read through the already-declared `/api/me/` `groups` field ([[API]]) and Django's own Group-membership check. No caching layer sits between a grant and its enforcement ([[adr-06-cache]]).

5. This is a doctrine addition, not a reversal. Cognito remains authentication-only and RBAC remains exclusively Django Groups ([[adr-10-auth]] rules 1–2, unchanged); this ADR only narrows which routes a role-less session may reach and states the mechanism — `AccessRequest` + signal — by which a role stops being role-less.
