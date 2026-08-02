---
title: adr-10-auth
type: adr
category: backend
use_case: wiring login or the OIDC callback, writing a permission class, adding an /accounts/ route, keying a user row, reaching for a password path
created: 2026-07-10
modified: 2026-08-02
tags: [adr, auth, cognito, backend]
---

# ADR-10 — authentication

## CONTEXT

> Cognito authenticates and does nothing else. Every authorization decision is a Django Group, read in Django, per request.

## ASSERTIONS

1. AWS Cognito is the only authentication provider, and it authenticates only. There is no second IdP and no home-grown password authentication in production; the OIDC flow is owned by [[AUTH]].
2. Authorization and RBAC live in Django. Roles are Django Groups enforced by DRF permission classes ([[BACKEND]]); Cognito groups and custom-claims-as-roles carry no authority here.
3. After token verification Django establishes its own session. Browser auth is Django session auth backed by the database ([[CACHE]]) because HTMX requires it ([[HTMX]]); token-only SPA auth is not the default.
4. The `/accounts/` prefix is the entire auth surface, routed to the backend by the ALB ([[INFRASTRUCTURE]]). Each of its routes is declared in [[API]] like any other ([[adr-03-api-and-backend]] rule 1).
5. User rows key on the Cognito `sub` claim; profile fields mirror Cognito standard attributes ([[GLOSSARY]], [[BD]]).
6. A DEBUG-only development auth path exists and produces the same Django user model and session mechanics as the real flow. A deploy-time system check hard-fails if it could run in production ([[AUTH]]) — the guard is a check, never a convention.
7. Cognito configuration enters [[VARIABLES]] before it is read and is sourced only from Secrets Manager `alvs/<env>/<project>/cognito`. The frontend receives zero Cognito variables ([[INFRASTRUCTURE]]).
8. One account is exempt from rule 1's no-password posture: the bootstrap superuser, the single row keyed `sub=bootstrap-admin`, created and rotated only by the `bootstrap_admin` management command from `DJANGO_SUPERUSER_EMAIL`/`DJANGO_SUPERUSER_PASSWORD` ([[VARIABLES]], [[BACKEND]]). Its purpose is break-glass access to `/admin/` ([[API]]) and nothing else; every other account keeps `set_unusable_password`.

## FORBIDDEN

- **NEVER** read a permission decision from a Cognito token or group (rule 2). Authority is a Django Group, and a claim that looks like a role is still not one.
- **NEVER** add a second authentication provider or a password path on `/accounts/` (rule 1). The bootstrap exception of rule 8 is one account at `/admin/` and widens nothing.
- **NEVER** serve an `/accounts/` route that has no [[API]] row ([[adr-03-api-and-backend]] rule 1). The auth surface is a contract like every other.
- **NEVER** let the development auth path survive into production behind a convention (rule 6). The guard is a deploy-time check that hard-fails.
- **NEVER** pass a Cognito variable or any secret to the frontend (rule 7). It receives `PUBLIC_*` only ([[adr-04-frontend-and-design-system]] rule 7).

## REJECTED

- **Cognito groups as roles** — the provider offers them and they would have arrived free with the token. They lost because authorization would then be decided by whoever administers the pool, in a place Django cannot test, and a token minted before a revocation would still carry the old authority. Closed for as long as rule 2 stands.
- **Token-only SPA auth** — no server session, the browser holding a JWT. Rejected because HTMX exchanges HTML over ordinary requests and needs the cookie ([[HTMX]]); it would reopen only if the frontend stopped being server-rendered.
- **A conventional guard on the development auth path** — a comment and a habit instead of a system check. Retired in favour of rule 6's hard failure: the one guard that cannot be forgotten is the one that breaks the deploy.

## RELATED

### related adrs

- [[docs/adrs/adr-20-authorization-lobby]] — what a session with zero Groups may reach, and how a Group is granted
- [[docs/adrs/adr-44-field-operational-roles]] — the six operational roles rule 2's Groups carry
- [[docs/adrs/adr-03-api-and-backend]] — rule 1, which rules 4's `/accounts/` surface
- [[docs/adrs/adr-13-m365-graph]] — the app-only Graph capability that is not a second IdP

### related files

- [[docs/AUTH]] — the OIDC flow, the session mechanics and the development path
- [[docs/API]] — the `/accounts/` and `/admin/` rows
- [[docs/VARIABLES]] — the Cognito configuration and the bootstrap credentials
- [[docs/BACKEND]] — permission classes and the management command
- [[docs/BD]] — the user row and its profile fields
