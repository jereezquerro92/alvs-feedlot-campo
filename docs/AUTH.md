---
title: AUTH
type: reference
status: active
created: 2026-07-10
tags: [harness, auth, cognito, backend]
---

# AUTH

Authentication doctrine for the template. Ruled by [[adr-10-auth]]. Authorization/RBAC design lives in [[BACKEND]]; the user table keys on the Cognito `sub` claim per [[BD]] and [[GLOSSARY]]; session storage follows [[CACHE]]; the `/accounts/` routing is owned by [[INFRASTRUCTURE]]; env/secret names are owned by [[VARIABLES]].

> [!important] The one-line split
> **Cognito answers "who are you?" — Django answers "what may you do?".** Identity is Cognito's only job. Every role, group, and permission decision is Django's, always. The two never trade places.

## Provider: Cognito, authentication only

AWS Cognito (a user pool per project, region us-east-1) is the sole authentication provider. There is no second IdP and no home-grown password store in production ([[adr-10-auth]] rule 1). Cognito verifies credentials and issues OIDC tokens; nothing more is delegated to it.

> [!warning] Cognito RBAC is prohibited
> Cognito **groups**, `cognito:groups`, and any **custom-claim-as-role** are banned ([[adr-10-auth]] rule 2). Roles are **Django Groups** checked by **DRF permission classes** ([[BACKEND]]). A permission decision that reads a Cognito claim is a defect, even if it "works". The only claims Django trusts from a token are **identity** claims (`sub`, `email`, and the standard profile attributes it mirrors), never authority.

## The real flow — OIDC authorization code

The browser talks to Cognito; Django brokers the exchange and then owns the session. The confidential client (client secret) means the code-for-token exchange happens server-side only.

1. An unauthenticated browser hits a protected resource and is sent to **`GET /accounts/login/`** (Django).
2. Django redirects to the Cognito hosted-UI **authorization** endpoint (`COGNITO_DOMAIN`) with `response_type=code`, `client_id=COGNITO_CLIENT_ID`, `scope=openid email profile`, `redirect_uri` = the project's own `/accounts/callback/` (derived from the project host — [[INFRASTRUCTURE]] — not a separate variable), and a fixed `identity_provider=Google` (owner-approved, hardcoded literal — no VARIABLES.md row, same precedent as adr-13 rule 6). That last param skips Cognito's hosted-UI IdP chooser and sends the browser straight to Google's account picker; email/password login against the user pool is unreachable by design. Cognito remains the sole authentication provider — Google is a federated IdP configured *inside* the Cognito user pool, not a second IdP Django talks to; the rest of this flow (steps 3–7) is unchanged.
3. Cognito authenticates the user and redirects back to **`GET /accounts/callback/?code=…`**.
4. Django exchanges the `code` at the Cognito **token** endpoint using `COGNITO_CLIENT_ID` + `COGNITO_CLIENT_SECRET` (server-to-server), then **verifies the ID token** against the pool's JWKS (`COGNITO_USER_POOL_ID`, `COGNITO_REGION`).
4b. Django then makes a **second, best-effort** call to Cognito's **`/oauth2/userInfo`** endpoint with the access token from step 4. This is not redundant: **the ID token does not carry attributes sourced from a federated IdP** (Google) that aren't among the small set Cognito always embeds — `picture` is the concrete case that surfaces it. This holds even with the Google IdP AttributeMapping set (`picture` → `picture`), the pool schema carrying the attribute, and the client requesting the `profile` scope — none of that puts `picture` on the ID token; `/oauth2/userInfo` is Cognito's own documented way to read the rest of the mapped attributes for the session. A failed/erroring `userInfo` call is logged and swallowed, never fatal — the avatar degrades to initials, but login must always succeed.

> [!note] Prior art
> `kodexArg/sociedad-rural-oeste-argentino` (SROA) hit the same ID-token gap and solved it the same way — a second `/oauth2/userInfo` call merged into the claims (there, persisted by django-allauth's cognito provider). This template took the mechanism, not the `django-allauth` dependency.
5. Django reads the **`sub`** and standard attributes from the verified token merged with the `userInfo` response, does a `get_or_create` on the user (see mapping below), and calls `django.contrib.auth.login()` — establishing a **Django DB-backed session** and its cookie.
6. From that point the browser is authenticated by the **Django session**, which is what HTMX mutations and fragments require ([[HTMX]], [[BACKEND]]). Cognito tokens are not replayed on every request; the session is authoritative.
7. **`POST /accounts/logout/`** (CSRF-protected; logout is a state change, so never GET) flushes the Django session and redirects through the Cognito logout endpoint so the hosted-UI session is cleared too.

> [!note] Why a Django session, not bearer tokens
> HTMX submits from the browser and relies on Django session auth + CSRF ([[HTMX]] rule 4). A token-only SPA pattern would break the hypermedia path. So the token is consumed once, at callback, and thereafter the session is the source of truth ([[adr-10-auth]] rule 3). Sessions use Django's DB-backed machinery — **no Redis** ([[CACHE]]).

### Endpoints (declared in [[API]] at stage 3)

These routes are **declared in [[API]]** (added there at step A3) but **not yet implemented in code**. Project construction (stage 3) writes the code against those existing rows — the row precedes the code ([[adr-03-api-and-backend]], no shadow routes). The surface, all under the ALB-routed `/accounts/` prefix ([[INFRASTRUCTURE]]):

| Route | Role |
|---|---|
| `/accounts/login/` | Kick off the OIDC redirect to Cognito |
| `/accounts/callback/` | Receive the code, verify the token, open the Django session |
| `/accounts/logout/` | Flush the Django session and clear the Cognito session (POST-only, CSRF-protected) |
| `/accounts/dev-login/` | **Development-only** dev login (below), wired only when `DEBUG` AND `AUTH_DEV_MODE` are both truthy; absent from any production image |

## Development mode — Cognito-free, same mechanics

Testing auth must not require a live Cognito pool. The template defines a **DEBUG-only local login backend** that ends in the exact same state as the real flow: the **same Django user model** (keyed on a `sub`) and the **same DB-backed session** — only the identity assertion differs.

**Mechanism.** A dev authentication backend `DevLoginBackend` plus a view at `/accounts/dev-login/`:

- The view accepts a chosen identity (a fixture user or a submitted email), synthesizes a stable `sub` for it, runs the **same `get_or_create` + attribute-mirror** that step 5 uses, and calls the same `django.contrib.auth.login()`. The resulting session, cookie, user row, and permission surface are indistinguishable from a real Cognito login — so Django Groups / DRF permissions ([[BACKEND]]) and HTMX session flows ([[HTMX]]) are exercised for real.
- It **replaces only step 1–5's Cognito legs** (redirect, code exchange, token verification). Everything downstream of `login()` is shared code.

**The hard guard (not a convention).** Two independent, structurally-enforced barriers:

1. **Wiring is double-gated.** `DevLoginBackend` is appended to `AUTHENTICATION_BACKENDS` and `/accounts/dev-login/` is added to the URLconf **only inside `if DEBUG and AUTH_DEV_MODE:`** — `AUTH_DEV_MODE` is the real switch, and `DEBUG` alone wires nothing. Production runs `DEBUG=false` and never sets `AUTH_DEV_MODE` ([[VARIABLES]]), so the backend and the route are simply **not present** in the running app.
2. **Django deploy-time system checks hard-fail.** Registered `django.core.checks` deploy checks raise **fatal Errors** — blocking `manage.py check --deploy`, which CI runs before every deploy AND the container entrypoint runs before serving — when `AUTH_DEV_MODE` is truthy in a deploy context (`users.E001`, whatever `DEBUG` says) or when `DEBUG` itself is truthy there (`users.E002`, the path that would wire dev-login). A production task with either switch on **cannot boot** — it is caught at deploy and at startup, not left to discipline.

`AUTH_DEV_MODE` is a **local-only, non-secret** switch ([[VARIABLES]]); it exists only in local `.env`. It never appears in a cloud task definition, and even if it did, guard #2 would refuse the deploy and the boot.

## The split-origin cookie bridge

The Astro origin calls the API with the session cookie ([[adr-10-auth]] rule 3), which fixes three settings decisions:

- **`CORS_ALLOW_CREDENTIALS = True` is a constant in code, never env** — a structural consequence of session auth: a whitelisted origin still cannot send or receive cookies without it. Which origins are allowed stays env-driven (`CORS_ALLOWED_ORIGINS` / `CSRF_TRUSTED_ORIGINS`, [[VARIABLES]]).
- **Cookies keep Django's `SameSite=Lax` default.** Locally `localhost:4321 → localhost:8000` is same-site (browsers ignore ports for site comparison), and in cloud both services sit behind the one ALB-routed domain ([[INFRASTRUCTURE]]), so `Lax` holds in both layouts; `SameSite=None` would only become necessary if the frontend ever moved to a different registrable domain, and that would be its own decision here.
- **`CSRF_COOKIE_HTTPONLY` stays `False`** (Django's default) on purpose: the browser reads the `csrftoken` cookie and returns it as the `X-CSRFToken` header on unsafe methods. The fetch pattern the frontend uses is documented in [[FRONTEND]].

## User-model mapping

The user row and its profile fields are shaped so Cognito claims and DRF serializers share names with zero translation ([[BD]] "User identity", [[GLOSSARY]]).

| Django user field | Source claim | Note |
|---|---|---|
| `sub` (primary identity key) | Cognito `sub` | Immutable, never recycled; the key both flows write ([[GLOSSARY]] forbids `cognito_id` / `uid` / `user_uuid`) |
| `email` | `email` | Standard attribute name, unchanged |
| `given_name` | `given_name` | Mirrors the Cognito standard attribute |
| `family_name` | `family_name` | Mirrors the Cognito standard attribute |

- Both the real callback (step 5) and dev login run the **same** `get_or_create(sub=…)` + attribute copy — the only difference is where the claims come from.
- Authorization data (**Django Groups**, DRF permissions) is assigned and stored **in Django**, never derived from a claim ([[adr-10-auth]] rule 2).

## Variables and secrets

All Cognito configuration is declared in [[VARIABLES]] (rows added before this doc referenced them) and sourced only from Secrets Manager `alvs/<env>/<project>/cognito` ([[INFRASTRUCTURE]] Secrets): `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, `COGNITO_CLIENT_SECRET`, `COGNITO_DOMAIN`, `COGNITO_REGION`, plus the local `AUTH_DEV_MODE` switch.

> [!warning] Zero Cognito on the frontend
> The Astro task receives **no** Cognito variable and **no** secret of any kind ([[adr-10-auth]] rule 7, [[VARIABLES]]). The frontend only follows Django's redirects and carries the session cookie; it never sees a client secret, a token, or a pool ID.

## Authorization lobby

Ruled by [[adr-20-authorization-lobby]]. A Cognito login opens a Django session, but a session alone is not enough to reach the app: every route requires the session AND membership in at least one Django Group, except `/` — the lobby ([[GLOSSARY]]: lobby) — which alone admits both an anonymous visitor and a role-less authenticated session.

### The `AccessRequest` model

`AccessRequest` ([[GLOSSARY]]) lives in the `users` app alongside the `sub`-keyed user model it authorizes — one row per user. Its `role` field ([[GLOSSARY]]) is a nullable `ForeignKey` to Django's own `Group`; `null` means the request is pending/unassigned. Setting `role` is an admin-only act performed in Django admin — never a self-service form, never a field any user-facing endpoint can write.

### From a grant to a Group membership

A `post_save` signal on `AccessRequest` mirrors a non-null `role` write into `user.groups`, adding the user to the granted `Group`. The signal is the only path from an `AccessRequest` row to actual authority — the row grants nothing on its own. Enforcement reads Group membership, exactly as the rest of RBAC does ([[adr-10-auth]] rule 2); `AccessRequest` never becomes a second, parallel source of authority.

### The bootstrap allowlist

Ruled by [[adr-21-bootstrap-allowlist-grant]]. `AUTH_BOOTSTRAP_ALLOWLIST` ([[GLOSSARY]], [[VARIABLES]]) holds comma-separated `email:group` pairs (group omitted → `admins`); `settings.py` parses it into an email→group map, empty when unset. In the shared provisioning path both login routes run — `upsert_user_from_claims`, the same `get_or_create` the real callback and dev-login share — an allowlisted email whose `AccessRequest.role` is still null gets that `role` filled, and the ordinary [[adr-20-authorization-lobby]] signal mirrors it into `user.groups`. The account escapes the lobby on its first request after first login, with no admin step and no re-login; the check re-runs on every login, so an entry added later grants on the next login. A non-null `role` is never touched (the admin stays authoritative), matching is case-insensitive on the email, and a pair naming a missing Group logs a warning and skips — a typo never breaks login and never creates a Group.

### The lobby, `/`

A role-less authenticated session sees the pending-authorization legend on `/`, rendered from the `lobby_pending` message key ([[GLOSSARY]], [[LOCALIZATION]]) — the key is English; its Spanish rendered value belongs to the i18n layer, not to this document. Re-evaluation is per-request over the existing Django session: once an admin grants a role, the very next request — a plain refresh — carries the new Group membership and every other route opens normally. No token is re-minted and no cache sits between the grant and its enforcement ([[adr-06-cache]]).
