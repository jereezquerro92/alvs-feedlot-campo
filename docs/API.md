---
title: API
type: reference
status: active
created: 2026-07-10
tags: [harness, api, ssot]
---

# API

Single source of truth for every HTTP endpoint in the system. Backend rules live in [[BACKEND]]; frontend consumption rules in [[FRONTEND]].

**An endpoint is valid if and only if it is declared in this file** ([[adr-03-api-and-backend]]). No route may exist in code without a row here. Nothing enters [[TDD]] or `models.py` without passing through this file first. An undeclared route found in code is a defect, regardless of whether it works.

> [!note] Enforcement
> The hook `hooks/check_api.py` (PostToolUse) diffs every written `urls.py` route literal against this table and blocks undeclared segments. `hooks/load_ssot.py` (SessionStart) injects this file and [[PRD]] into context at session start; `hooks/require_api_read.py` (UserPromptSubmit) forces a fresh read whenever a prompt mentions the API. `hooks/dispatch_guardians.py` (PostToolUse) routes changes to this file or the route surface (`urls.py`, `views.py`, `viewsets.py`, `serializers.py`, `models.py`, Django templates) to the guardian subagent `agents/astro-drf-aws-api.md`, which enforces the format and change protocol below.

## Workflow position

`plan → API.md → [[TDD]] → models.py → rest of DRF`

This file is written **before** tests and **before** models. Why: the endpoint table is the cheapest artifact to review and the most expensive one to get wrong downstream.

## Declaration format

Every endpoint is one row in the table below, with these columns:

| Column | Rule |
|---|---|
| Method | One HTTP verb per row. |
| Path | English only ([[LOCALIZATION]]). Trailing slash. Under a backend prefix (see below). |
| View/ViewSet | Class name, named per [[GLOSSARY]]. |
| Serializer | Class name for JSON DRF views with a model serializer; **`—` when no serializer class exists** — either an HTML fragment view ([[HTMX]]) or a JSON view with no model to serialize (e.g. a status-only probe). The Description cell states which. |
| Auth | `none`, `session`, `token`, or the permission class name. Prefer `session` for browser HTMX mutations. |
| Description | One line. What, not how. For fragments, say **HTML fragment** and the swap role (e.g. list region, form errors). |

Rules:

- All backend paths live under the prefixes the ALB routes to the backend: `/api/`, `/admin/`, `/accounts/`, `/ws/` — routing is owned by [[INFRASTRUCTURE]]. A path outside these prefixes belongs to the Astro service and MUST NOT appear here.
- Names (viewsets, serializers, path segments) follow [[GLOSSARY]]. New nouns are added there first.
- Complex request/response contracts (bodies, error shapes, pagination, fragment root element / `hx-target` id) go in a **Contracts** subsection below the table, one heading per endpoint, linked from the Description cell — never inline in the table.
- Auth defaults and caching behavior per endpoint follow [[CACHE]] (authenticated responses are `no-store` by default).

Routes that return HTML fragments ([[HTMX]]) are endpoints like any other and MUST be declared here with the same columns; a fragment route absent from this table is invalid ([[adr-05-htmx]]). **Django renders those fragments** — do not list an Astro route as a fragment producer. JSON and HTML for the same resource are separate rows when both exist.

## Endpoints

| Method | Path | View/ViewSet | Serializer | Auth | Description |
|---|---|---|---|---|---|
| GET | `/api/health/` | `HealthCheckView` | — | none | Liveness probe for ALB target group; returns 200 when the service is up. |
| GET | `/accounts/login/` | `LoginView` | — | none | Starts the OIDC authorization-code redirect straight to Google via Cognito's federated IdP, skipping the hosted-UI chooser ([[AUTH]]). Contract below. |
| GET | `/accounts/callback/` | `CallbackView` | — | none | OIDC redirect target: verifies the ID token, fetches `/oauth2/userInfo` for federated-IdP attributes (`picture`), mirrors identity claims, opens the Django session ([[AUTH]]). Contract below. |
| POST | `/accounts/logout/` | `LogoutView` | — | session | Flushes the Django session and redirects through the Cognito logout endpoint ([[AUTH]]). POST-only (CSRF-protected); a session flush is a state change. Contract below. |
| GET | `/accounts/dev-login/` | `DevLoginView` | — | none | **DEBUG-only** dev login; same `get_or_create` + session as the real flow, absent from production images ([[AUTH]]). Contract below. |
| GET | `/api/me/` | `MeView` | `UserSerializer` | session | Current session identity — the logged-in user and its Django groups. Contract below. |
| PATCH | `/api/me/` | `MeView` | `UserSerializer` (write fields: `nickname`, `avatar_visible`, `theme_config`) | session | Partial update of the profile-owned fields. Read-only fields (`sub`, `email`, `given_name`, `family_name`, `picture`, `groups`) are rejected if present with a non-matching value — `400`, never silently ignored. `no-store`. |
| GET | `/api/restricted/` | `RestrictedView` | — | session; `IsInAdminsGroup` | RBAC probe: 200 for members of the `admins` group, 403 otherwise — decided by Django Groups, never a Cognito claim ([[adr-10-auth]]). Contract below. |
| GET | `/api/m365/hello/` | `HelloView` | — | none (`AllowAny`, named exception, [[adr-13-m365-graph]]) | App-only Microsoft Graph read of workbook cell A1; plain text `Hello` on success. Contract below. |
| GET | `/api/m365/world/` | `WorldView` | — | none (`AllowAny`, named exception, [[adr-13-m365-graph]]) | App-only Microsoft Graph read of workbook cell C3; plain text `World` on success. Contract below. |
| POST | `/api/router/route/` | `RouteView` | `RouteRequestSerializer` | session; `CanUseRouter` (`admins` or `ai_operators` Django group) | Chatbot **choosing tier**, async ([[adr-16-async-mandatory]]): takes a user utterance, returns one of the four closed outcomes only — never free text ([[adr-15-chatbot-two-tier]]). RBAC gate: authenticated AND member of `admins` or `ai_operators` — `ai_operators` is router-only, never added to any other permission class. Per-user cooldown (`THROTTLE_COOLDOWN_SECONDS`, default `2`) plus a silent, async rate-abuse block (`ROUTER_RATE_*`, [[VARIABLES]]) — both return `429`, indistinguishable to the caller. Contract below. |
| GET | `/admin/` | `admin.site.urls` (mount) | — | session; `is_staff` (Django admin's own gate) | Django admin site — the whole `django.contrib.admin` sub-tree mounted at the `/admin/` prefix (owner decision 2026-07-14, issue #83). One row for the mount; its internal routes are Django's own, not per-row API surface. Anonymous requests redirect to `/admin/login/`. That login form authenticates exactly one account: the bootstrap superuser ([[adr-10-auth]] rule 8 named exception) — every other user has an unusable password and enters only via the Cognito session flow. Authenticated admin responses are `no-store` ([[CACHE]]). |

## Contracts

All rows below are authentication/identity surface; every response carries an explicit `Cache-Control` and is **`no-store`** — the `/accounts/` routes mutate or read the session, and `/api/me/` and `/api/restricted/` are authenticated ([[CACHE]], authenticated → `no-store`). Full flow and guards live in [[AUTH]]; these entries state only the endpoint contracts.

### GET /accounts/login/

Redirect kickoff. Issues a 302 to the Cognito hosted-UI authorization endpoint with `response_type=code`, `client_id`, `scope=openid email profile`, `redirect_uri` = this project's `/accounts/callback/` (derived from the host, [[INFRASTRUCTURE]] — not a variable), and a fixed `identity_provider=Google` (hardcoded literal, owner-approved — no VARIABLES.md row, [[AUTH]]) that sends the browser straight to Google's account picker instead of Cognito's hosted-UI IdP chooser. No body. `no-store`. **Error shape (two branches):** if `COGNITO_CLIENT_ID`, `COGNITO_DOMAIN`, or `COGNITO_USER_POOL_ID` is unset/empty, the view never builds an authorize URL. **(a)** When `DEBUG` and `AUTH_DEV_MODE` are both truthy, it 302s to `/accounts/dev-login/` — the local development path, same user-model and session mechanics as the real flow ([[adr-10-auth]] rule 6), so localhost stays usable without any Cognito configuration. **(b)** Otherwise (production, or dev auth disabled) it returns `500` rendering a minimal HTML template (`users/cognito_not_configured.html`) naming only the missing variable name(s), never their values and never a silent redirect to a broken authorize URL ([[AUTH]]).

### GET /accounts/callback/

OIDC redirect target, query `?code=…` (plus the CSRF `state` it issued at login). Exchanges the code server-to-server, verifies the ID token against the pool JWKS, then makes a **second, best-effort** call to Cognito's `/oauth2/userInfo` with the access token to pick up attributes the ID token never carries for a federated IdP (notably Google's `picture` — [[AUTH]]) and merges them into the claims before mirroring. Runs `get_or_create(sub=…)` + attribute mirror, calls `django.contrib.auth.login()`, then 302s to the post-login destination `LOGIN_REDIRECT_URL` (default `/` — the single ALB origin in cloud; the frontend origin locally, [[VARIABLES]]). On successful login the backend sets the `theme` cookie from the user's `theme_config` (non-HttpOnly, `SameSite=Lax`, `Secure` mirrors CSRF) so SSR renders the user's theme with no flash ([[DESIGN-SYSTEM]]). Error shape: an invalid/expired `code` or a failed `state`/token verification returns a 4xx auth-error response (no session opened); a failed/erroring `userInfo` call is logged and swallowed — login still succeeds with whatever the ID token alone carried. `no-store`.

### POST /accounts/logout/

Flushes the Django session, then 302s through the Cognito logout endpoint (with `logout_uri` = `LOGOUT_REDIRECT_URL`, [[VARIABLES]]) so the hosted-UI session is cleared too. When Cognito is unconfigured (local dev), it skips the Cognito hop and 302s straight to `LOGOUT_REDIRECT_URL` (the frontend origin locally). **POST only, CSRF-protected** — logout is a state change; a GET would allow drive-by logout from any third-party page (Django itself dropped GET logout in 5.0). GET returns 405. Safe to POST without an active session (no-op flush, still redirects). The frontend logout affordance is a small form/fetch POST carrying the CSRF token, never an `<a>`. `no-store`.

### GET /accounts/dev-login/

**Development-only** and present in the URLconf only inside `if DEBUG and AUTH_DEV_MODE:` — it does not exist in a production image. Accepts a chosen identity (a fixture user or a submitted email), synthesizes a stable `sub`, runs the **same** `get_or_create` + attribute mirror + `login()` as the callback, then 302s to `LOGIN_REDIRECT_URL` (the frontend origin locally, [[VARIABLES]]) — the same post-login destination as the real callback. On successful login the backend sets the `theme` cookie from the user's `theme_config` (non-HttpOnly, `SameSite=Lax`, `Secure` mirrors CSRF) so SSR renders the user's theme with no flash ([[DESIGN-SYSTEM]]). Two structural guards ([[AUTH]], [[adr-10-auth]] rule 6): (1) wiring requires BOTH `DEBUG` and `AUTH_DEV_MODE` truthy; (2) `django.core.checks` deploy checks raise fatal Errors — failing `manage.py check --deploy`, which the container entrypoint runs before serving — when `AUTH_DEV_MODE` is truthy in a deploy context (`users.E001`) or when `DEBUG` is (`users.E002`). `no-store`.

### GET /api/me/

Returns the current session user via `UserSerializer`: `{ sub, email, given_name, family_name, picture, groups: [<name>, …], theme_config }` — `picture` mirrors the standard Cognito attribute of that name ([[adr-10-auth]] rule 5: profile fields mirror Cognito standard attributes), sourced from `/oauth2/userInfo` rather than the ID token for a federated IdP ([[AUTH]]); empty string when absent. `groups` are Django group names ([[adr-10-auth]]: authority is Django, never a Cognito claim). `theme_config` is the per-user appearance blob ([[GLOSSARY]]: `theme_config`) — closed keys `{ mode, bgPreset, colors, radius }`, all optional; a key never set by the user is simply absent, no defaults injected server-side ([[DESIGN-SYSTEM]]). 200 when a session exists; unauthenticated requests are rejected per the view's `session` auth (no user payload). `no-store`.

### PATCH /api/me/

Partial update, same view as the `GET`. Session auth, `no-store` ([[CACHE]] rule 4 — authenticated, personalized). Body accepts `nickname` (string, blank allowed — blank means "unset, fall back to Cognito name"), `avatar_visible` (boolean), and/or `theme_config` (object). Any other key present is a validation error (`400`, DRF default shape); this is a profile-fields endpoint, not a generic user-object PATCH. 200 returns the same shape as `GET /api/me/`, fields updated.

**`theme_config` validation** ([[GLOSSARY]]: `theme_config`, `theme`, `mode`, `bgPreset`; [[DESIGN-SYSTEM]]): the blob accepts only the closed key set `mode`, `bgPreset`, `colors`, `radius` — an unknown key is a `400`. `mode` is the enum `"light"|"dark"`; `bgPreset` is the enum `"default"|"melt"`; either an out-of-enum value is a `400`. `colors` is an object whose values (`background`, `primary`, `secondary`, `accent`, all optional) must each match `^(#[0-9a-fA-F]{3,8}|rgb(a)?\(.*\)|hsl\(.*\)|oklch\(.*\))$` with no `;`, `{`, `}`, `<`, `>`, `"`, `'`, and no `url`/`expression` substring — a non-matching value is a `400`. `radius` must match `^[0-9]*\.?[0-9]+(px|rem|em|%|vh|vw|ch)$` (e.g. `"0.625rem"`) — a non-matching value is a `400`, mirroring the frontend's `RADIUS_PATTERN`. On success the backend saves the merged blob to `User.theme_config` and **refreshes the non-HttpOnly `theme` cookie** (`Set-Cookie`, `Path=/`, `SameSite=Lax`, `Secure` mirroring `CSRF_COOKIE_SECURE`, `Max-Age` ~31536000) with `encodeURIComponent(JSON.stringify(blob))` so the next SSR render picks up the change with no flash ([[DESIGN-SYSTEM]]). `no-store` still applies to the JSON body; the cookie is not itself cached data.

### GET /api/restricted/

RBAC probe, status-only (no model serializer — hence `—`): 200 with a minimal JSON body (`{ "detail": "ok" }`) for members of the Django `admins` group, **403** otherwise. Enforced by the DRF permission class `IsInAdminsGroup` on top of `session` auth; the decision reads Django group membership only, never a token claim ([[adr-10-auth]] rule 2). `no-store`.

### GET /api/m365/hello/

Deliberate `AllowAny` demo endpoint ([[adr-13-m365-graph]]): acquires an app-only Graph access token via client_credentials (no user, no browser flow, no stored token), GETs workbook cell A1, returns its literal text (`Hello`) as `text/plain`, `no-store`. A token-acquisition failure returns `502 graph_auth_failed`; a Graph `403` (missing admin consent) returns `502 graph_forbidden`; a Graph `429` returns `503 graph_throttled` — never a 500 traceback.

### GET /api/m365/world/

Same contract as `/api/m365/hello/`, reading cell C3 (`World`).

### POST /api/router/route/

Chatbot **choosing tier** ([[adr-15-chatbot-two-tier]]), an `async def` view riding the existing ASGI server ([[adr-16-async-mandatory]]). RBAC gate ([[adr-10-auth]] rule 2): `IsAuthenticated` + `CanUseRouter` — the requesting user must be a member of the Django group `admins` or `ai_operators`; `ai_operators` is a router-only group, never accepted by any other permission class in this codebase. Request body: `{ "utterance": "<user text>" }` via `RouteRequestSerializer`. The server builds the closed, permission-filtered menu **before** invoking the model (`build_menu`, [[adr-15-chatbot-two-tier]] rule 2); inference (`get_inference_client`: real Bedrock in any non-DEBUG process, the deterministic mock only under `DEBUG` — [[tdd-03-router-bedrock-inference]], #253) is called through `asgiref.sync_to_async` ([[adr-16-async-mandatory]] rule 4). One `IntentQuery` audit row is persisted per call, including a throttled or permission-denied reject for an already-authenticated (but non-member) user — an unauthenticated (401/403, no session) request has no `user` FK to write against and is not audited.

Success response — one of the four outcomes ([[CHATBOT]] — the four outcomes), `200`. `query_id` is the `IntentQuery` row's integer primary key (`<int>`, not a UUID — no SSOT requires one):
- `{ "outcome": "Action", "query_id": <int>, "action": { "kind": "navigate"|"confirm", "target": "<path>", "label": "<registry phrase>" } }`
- `{ "outcome": "Answer", "query_id": <int>, "action": { "kind": "confirm", "target": "<path>", "label": "<registry phrase>" } }` — reserved for a future GET-answering registry kind; the landed `Intent.KIND_CHOICES` does not yet offer it, so no registry row can produce it today.
- `{ "outcome": "Escalate", "query_id": <int> }`
- `{ "outcome": "NO_MATCH", "query_id": <int> }`

No prose beyond the registry-authored `label` ever ships (rule 5). Error shape: a model output outside the closed menu is a **hard reject** — `422 { "detail": "router_hard_reject" }`, logged as a fault, never repaired, never defaulted, never retried into a nearest match (rule 2). The kill switch short-circuits to the reserved `disabled` outcome, never an error: `ROUTER_ENABLED=false` returns `200 { "outcome": "disabled", "query_id": <int> }` before any inference call, zero inference calls made, still persists its audit row. A throttled burst (`CooldownThrottle`, `THROTTLE_COOLDOWN_SECONDS`, default `2`) returns `429` (audited, `choice="throttled"`). An inference-transport failure (Bedrock unreachable: network, IAM, or model access) degrades the router surface only — `503 { "detail": "router_unavailable", "query_id": <int> }`, audited (`choice="unavailable"`), never a backend crash and never a defaulted or retried choice ([[tdd-03-router-bedrock-inference]] decision 4, #253). `no-store` ([[CACHE]], authenticated → `no-store`).

**Silent rate-abuse block (#371):** at the end of a successful handler pass, an async evaluation ([[adr-16-async-mandatory]]) checks the requesting user's recent message rate against `ROUTER_RATE_THRESHOLD_PER_MINUTE` (default `20`/min) — but only when there has been router activity from that user within the last `ROUTER_RATE_IDLE_SKIP_SECONDS` (default `20`s); the common idle case evaluates nothing. Crossing the threshold marks the user blocked for `ROUTER_RATE_BLOCK_SECONDS` (default `300`s); every request from a blocked user returns a bare `429` with an empty body — no `detail`, no reason, deliberately indistinguishable from the `CooldownThrottle` reject above (audited, `choice="rate_blocked"`). This is enforcement only: it reads and writes no Group membership and narrows no permission ([[adr-15-chatbot-two-tier]] rule 3). State lives in the shared `DatabaseCache` ([[CACHE]]) — no Redis ([[adr-06-cache]]).

This supersedes the prior `{ "action": "<enum member>", "slots": {...} }` shape recorded when the row was first added — no code ever shipped that contract.

## Change protocol

- Adding or changing a row is an explicit, reviewable act: its own commit (or its own hunk in review), never smuggled into an implementation diff.
- **Removing an endpoint requires removing its row first.** The code deletion follows the row deletion, not the other way around.
- A row change invalidates the corresponding [[TDD]] entry; update it in the same cycle.
