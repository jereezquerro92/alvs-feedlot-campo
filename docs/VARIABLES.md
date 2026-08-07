---
title: VARIABLES
type: reference
category: harness
use_case: reading or adding an environment variable
created: 2026-07-10
modified: 2026-08-07
tags: [doc, harness, variables, ssot]
---

# VARIABLES

The environment-variable **SSOT**. Every variable either backend or frontend code reads is declared here first.

> [!warning]
> **A variable used in code but not declared here does not exist.** Same doctrine as [[API]]. Enforced by the hook `hooks/check_variables.py` (PostToolUse), which watches `.env*` files and env reads in code against this table. Companion skills are still stage 2 work — TBD.

> [!warning]
> **A secret's source is one path shape: `alvs/<env>/<project>/<component>`** — the fact this doc owns, per [[INFRASTRUCTURE]]. That secrets live only in AWS Secrets Manager is [[adr-50-initial-stack]] rule 6; that the frontend receives only `PUBLIC_*` and never a secret is [[adr-52-frontend-and-design-system]] rule 7. Local `.env` (git-ignored) holds dev-only values mirroring the names declared here.

## Declaration format

Every variable is one row. Sources: Secrets Manager key, plain task env, or `.env` local.

## Declared variables (template starting set)

Baseline seeded from the SROA precedent — extend per project, never prune blindly.

### Shared

Read by both services and by tooling (CI, compose). Non-secret identity values.

| Name | Scope | Envs | Secret? | Source | Description |
|---|---|---|---|---|---|
| `PROJECT_SLUG` | backend + CI | dev/prod/local | no | plain task env; `.env` local | Project slug — the `<project>` in every AWS name ([[INFRASTRUCTURE]], [[GLOSSARY]]). This template's reference value: `astro-drf-aws`. Read by `backend/config/settings.py` and by `.github/workflows/deploy-prod.yml`; the frontend never reads this name directly — it receives the derived `PUBLIC_PROJECT_SLUG` below ([[VARIABLES]] Frontend) |
| `BASE_DOMAIN` | backend + frontend | dev/prod/local | no | plain task env; `.env` local | Base domain (`grupoalvs.com`). **The project host is NOT derived from the slug.** It is the `PROJECT_HOST` GitHub Actions repository variable, read at deploy time and required by preflight ([[GH]], [[adr-48-derived-project-deploy-identity]] rules 1–2) — this project is served at `feedlot.grupoalvs.com` while its slug is `feedlot-campo`, and the `<slug>.<domain>` guess this row used to state sent the frontend to a host that does not resolve (issue #72) |

#### Sanctioned `PROJECT_SLUG` consumption points

The reference value `astro-drf-aws` is a literal exactly once per surface — everywhere else it is reached through `PROJECT_SLUG` (or its frontend-derived form `PUBLIC_PROJECT_SLUG`), never re-typed. This is the full inventory the `tests/test_project_slug_hardcode.py` guard (issue #133) enforces:

- **`.env.example`** — `PROJECT_SLUG=astro-drf-aws`, the local dev seed.
- **`backend/config/settings.py`** — `PROJECT_SLUG = _env("PROJECT_SLUG", "astro-drf-aws")`, the single fallback default.
- **`compose.yaml`** — `${PROJECT_SLUG:-astro-drf-aws}` (Compose project `name:` and the `PUBLIC_PROJECT_SLUG` passthrough to the frontend container).
- **`.github/workflows/deploy-prod.yml`** — the one seed line `PROJECT_SLUG: astro-drf-aws`; every other job reads `${{ env.PROJECT_SLUG }}` / `${PROJECT_SLUG}`, never a second literal. The four opaque ARNs (`SECRET_DJANGO`/`SECRET_DB`/`SECRET_COGNITO`/`SECRET_MSGRAPH`) are a distinct exception — AWS-random-suffix values baked at provisioning time, not derivable from the slug (issue #129).
- **`frontend/src/layouts/Base.astro`**, **`frontend/src/pages/index.astro`** — `process.env.PUBLIC_PROJECT_SLUG ?? "astro-drf-aws"`, the frontend-side fallback.
- **Markdown docs** (`*.md`) — narrative/reference use is exempt everywhere; this table and [[GLOSSARY]] are themselves that reference.
- **Live-doc block headers** ([[adr-17-live-doc-backlinks]]) — the generated `LIVE-DOC:START — astro-drf-aws live-doc …` line stamped by the linker, not a hand-typed hardcode.
- **`.claude/hooks/graph_first.py`** — carries `astro-drf-aws` as part of a different identifier (the codebase-memory-mcp project id) — not this variable, exempted by name in the guard test.
- **`.claude/kdx-park.json`** — carries `kodexArg/astro-drf-aws` as the `repo` routing target for `kdx-draft-issue` park mode (harness tooling, not app runtime); the slug portion is a shipped reference default like every other seed here, and a cloned template inherits `kodexArg`'s park target until it re-points this file — exactly as it re-points `PROJECT_SLUG` (the harness-tooling carve-out rationale of #307, extended). It is exempted by name in the guard test.
- **Guardian-name occurrences** — `astro-drf-aws-prd`, `astro-drf-aws-adr`, `astro-drf-aws-api` (e.g. in `.claude/hooks/dispatch_guardians.py`, `tests/test_guardian_identity_triangle.py`) are an allowed SEPARATE naming axis, not this variable — an agent identity, guarded on its own by `tests/test_guardian_identity_triangle.py`, not by this test.

### Backend

| Name | Scope | Envs | Secret? | Source | Description |
|---|---|---|---|---|---|
| `DB_HOST` | backend | dev/prod/local | yes | `alvs/<env>/<project>/db` (`host`); `.env` local | Database host |
| `DB_PORT` | backend | dev/prod/local | yes | `alvs/<env>/<project>/db` (`port`); `.env` local | Database port (5432) |
| `DB_NAME` | backend | dev/prod/local | yes | `alvs/<env>/<project>/db` (`dbname`); `.env` local | Database name |
| `DB_USER` | backend | dev/prod/local | yes | `alvs/<env>/<project>/db` (`username`); `.env` local | Database user |
| `DB_PASSWORD` | backend | dev/prod/local | yes | `alvs/<env>/<project>/db` (`password`); `.env` local | Database password |
| `CACHE_URL` | backend | dev/prod | yes | `alvs/<env>/<project>/valkey` (`url`); omitted locally | Redis-protocol URL for ElastiCache Valkey (Django shared cache, [[CACHE]] layer 2, [[adr-06-cache]]). Absent locally — settings keep `DatabaseCache`. Declared ahead of the Valkey wiring implementation |
| `SECRET_KEY` | backend | dev/prod/local | yes | `alvs/<env>/<project>/django`; `.env` local | Django secret key |
| `ALLOWED_HOSTS` | backend | dev/prod/local | yes | `alvs/<env>/<project>/django`; `.env` local | Django allowed hosts list. **Prod value must also include this project's own Cloud Map hostname — `backend.<PROJECT_SLUG>-<env>.local`, here `backend.feedlot-campo-prod.local`** — alongside the public domain, because the frontend's SSR fetch reaches the backend by that internal host, never by the public domain (2026-07-13 fix). Omitting it does not break the site: Django answers the SSR call with `400` (`DisallowedHost`), so every page renders as if the visitor were anonymous — a logged-in user with a role is bounced back to the lobby and the failure looks like broken login (issue #75). This row previously named the **template's** Cloud Map host literally, which is how the omission survived provisioning |
| `DEBUG` | backend | dev/prod/local | yes | `alvs/<env>/<project>/django`; `.env` local | Django debug flag (never true in prod) |
| `CORS_ALLOWED_ORIGINS` | backend | dev/prod/local | yes | `alvs/<env>/<project>/django`; `.env` local | CORS origin allowlist |
| `CSRF_TRUSTED_ORIGINS` | backend | dev/prod/local | yes | `alvs/<env>/<project>/django`; `.env` local | CSRF trusted origins — carries the split local origins ([[DOCKER]]) |
| `AWS_STORAGE_BUCKET_NAME` | backend | dev/prod | yes | `alvs/<env>/<project>/s3` | Media S3 bucket ([[INFRASTRUCTURE]]) |
| `AWS_S3_REGION_NAME` | backend | dev/prod | yes | `alvs/<env>/<project>/s3` | S3 region (us-east-1) |
| `MEDIA_URL` | backend | dev/prod/local | yes | `alvs/<env>/<project>/s3`; `.env` local | Django media URL prefix — vestigial in dev/prod, where the S3 storage backend issues presigned URLs directly per object; no CDN in this template ([[CACHE]], [[INFRASTRUCTURE]]) |
| `COGNITO_USER_POOL_ID` | backend | dev/prod/local | yes | `alvs/<env>/<project>/cognito`; `.env` local | Cognito user pool ID — the OIDC identity source ([[AUTH]], [[INFRASTRUCTURE]]). **Not always a dedicated per-project pool**: for `alvs-feedlot-campo` prod this value is `us-east-1_YrRbIScNL`, the pre-existing shared `alvs-org-pool`, since this project's app client was created there rather than in a new pool ([[AUTH]], `docs/INVENTORY.md`) |
| `COGNITO_CLIENT_ID` | backend | dev/prod/local | yes | `alvs/<env>/<project>/cognito`; `.env` local | Cognito app client ID (confidential OIDC client) ([[AUTH]]) |
| `COGNITO_CLIENT_SECRET` | backend | dev/prod/local | yes | `alvs/<env>/<project>/cognito`; `.env` local | Cognito app client secret — authorization-code token exchange ([[AUTH]]) |
| `COGNITO_DOMAIN` | backend | dev/prod/local | yes | `alvs/<env>/<project>/cognito`; `.env` local | Cognito hosted-UI / OIDC issuer domain ([[AUTH]]). For `alvs-feedlot-campo` prod this is the shared `https://alvs-auth.auth.us-east-1.amazoncognito.com` domain of `alvs-org-pool`, not a project-specific hosted-UI domain — same shared-pool divergence as `COGNITO_USER_POOL_ID` above |
| `COGNITO_REGION` | backend | dev/prod/local | yes | `alvs/<env>/<project>/cognito`; `.env` local | Cognito user pool region (us-east-1) ([[AUTH]]) |
| `AUTH_DEV_MODE` | backend | local | no | `.env` local | Dev-login switch; wires the dev auth path only together with `DEBUG=true`. A deploy-time system check hard-fails when it is truthy in a deploy context (and when `DEBUG` is), so it can never run in cloud ([[AUTH]]) |
| `LOGIN_REDIRECT_URL` | backend | dev/prod/local | no | plain task env; `.env` local | Post-login destination for both the OIDC callback and the dev-login path. Defaults to `/` — correct in cloud, where the ALB serves the frontend and the backend from one origin. Locally the two run on split ports, so it is set to the frontend origin (`http://localhost:4321/`) to land the user back on the app after login ([[AUTH]], [[INFRASTRUCTURE]]) |
| `LOGOUT_REDIRECT_URL` | backend | dev/prod/local | no | plain task env; `.env` local | Post-logout destination. Defaults to `/` (single ALB origin in cloud); set to the frontend origin locally. In dev mode with Cognito unconfigured the logout skips the Cognito hop and redirects here directly ([[AUTH]]) |
| `USE_X_FORWARDED_PROTO` | backend | dev/prod | no | plain task env | When truthy, sets `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` so Django trusts the ALB's `X-Forwarded-Proto` and builds `https://` absolute URIs (OIDC `redirect_uri`, [[AUTH]]). Set only behind the ALB ([[INFRASTRUCTURE]]); never locally |
| `MSGRAPH_TENANT_ID` | backend | dev/prod/local | yes | `alvs/<env>/<project>/msgraph`; `.env` local | Entra single-tenant directory ID ([[adr-13-m365-graph]]) |
| `BEDROCK_REGION` | backend | dev/prod/local | no | plain task env; `.env` local | Bedrock inference region for the chatbot `router` (`us-east-1` — Nova Micro availability). Auth is task-role IAM, no key material; neither `AWS_S3_REGION_NAME` nor `COGNITO_REGION` is reused — both are service-scoped and secret-sourced |
| `MSGRAPH_CLIENT_ID` | backend | dev/prod/local | yes | `alvs/<env>/<project>/msgraph`; `.env` local | Entra app registration (client) ID for the app-only Graph flow ([[adr-13-m365-graph]]) |
| `MSGRAPH_CLIENT_SECRET` | backend | dev/prod/local | yes | `alvs/<env>/<project>/msgraph`; `.env` local | Entra app client secret — client_credentials token acquisition ([[adr-13-m365-graph]]) |
| `THROTTLE_COOLDOWN_SECONDS` | backend | dev/prod/local | no | plain task env; `.env` local | Cooldown window in seconds for `CooldownThrottle` (DRF throttle at rate `1/<period>`, per authenticated user, [[CACHE]] layer 2); default `2` (lowered from `30`, #371), `0` disables it — the local-dev escape hatch ([[GLOSSARY]] cooldown) |
| `UVICORN_WORKERS` | backend | dev/prod/local | no | plain task env (`ENV` default in `backend/Dockerfile`); `.env` local | Worker-process count passed as `--workers` to the uvicorn ASGI server launched by the `backend/Dockerfile` CMD; default `4` ([[REQUIREMENTS]], [[adr-16-async-mandatory]]) |
| `ECS_CONTAINER_METADATA_URI_V4` | backend | dev/prod | no | injected automatically by ECS (not a secret, never set by us) | The ECS task metadata endpoint. When present, settings fetches the task's private IPv4 at startup and appends it to `ALLOWED_HOSTS` so the ALB's by-IP health probe (`Host: <task-ip>:8000`) is not rejected as `DisallowedHost`. Fail-open: any fetch error leaves `ALLOWED_HOSTS` unchanged. Absent locally, so a no-op there ([[INFRASTRUCTURE]]) |
| `DJANGO_SUPERUSER_EMAIL` | backend | dev/prod/local | yes | `alvs/<env>/<project>/django`; `.env` local | Bootstrap superuser email, read directly via `os.environ` by the `bootstrap_admin` management command run on every container boot ([[BACKEND]]) |
| `DJANGO_SUPERUSER_PASSWORD` | backend | dev/prod/local | yes | `alvs/<env>/<project>/django`; `.env` local | Bootstrap superuser password, read directly via `os.environ` by the `bootstrap_admin` management command; rotates the existing row's password on every boot ([[BACKEND]]) |
| `AUTH_BOOTSTRAP_ALLOWLIST` | backend | dev/prod/local | no | `alvs/<env>/<project>/django`; `.env` local | Comma-separated `email:group` pairs ([[GLOSSARY]]) whose `AccessRequest.role` is auto-filled at first login (group omitted → `admins`); empty/unset disables the mechanism entirely. Treat as sensitive — it grants admin ([[AUTH]], [[adr-21-bootstrap-allowlist-grant]]) |
| `ROUTER_ENABLED` | backend | dev/prod/local | no | plain task env; `.env` local | Kill switch for the chatbot `router` choosing tier ([[CHATBOT]], [[adr-15-chatbot-two-tier]]): `false` short-circuits `POST /api/router/route/` to `200 { "outcome": "disabled", "query_id": <int> }` before any inference call (still persists the audit row; never a `503` — that status is reserved for inference-transport failure). Default `true`. Contract SSOT: [[API]] |
| `ROUTER_BEDROCK_MODEL_ID` | backend | dev/prod/local | no | plain task env; `.env` local | Bedrock model ID for the `router` choosing tier's constrained-decoding inference call ([[adr-15-chatbot-two-tier]]). **Must be the cross-region inference-profile form** — `us.amazon.nova-micro-v1:0`, not the bare `amazon.nova-micro-v1:0`, which is not on-demand invokable and fails with `ValidationException` ([[CHATBOT]] AccessDenied/ValidationException triage; grant shape in [[INFRASTRUCTURE]]). Reuses `BEDROCK_REGION` above for its region — no duplicate region variable added. The `boto3` + `asgiref.sync_to_async` call mechanism is owned by [[BACKEND]] ([[adr-16-async-mandatory]] rule 4), not this file |
| `ADVISOR_BEDROCK_MODEL_ID` | backend | dev/prod/local | no | plain task env; `.env` local | Bedrock model ID for the `advisors` **generative** tier ([[adr-27-advisors-generative]], [[adr-31-advisors-implementation]]) — distinct from the router because this tier generates prose (temperature 0.3), so a more capable model than Nova Micro is used. **Must be the cross-region inference-profile form** — e.g. `us.amazon.nova-lite-v1:0`, not the bare ID (not on-demand invokable, fails `ValidationException`). Reuses `BEDROCK_REGION` — no duplicate region variable. The `boto3` + `asgiref.sync_to_async` call mechanism is owned by [[BACKEND]] ([[adr-16-async-mandatory]] rule 4), not this file. Read only outside DEBUG; DEBUG uses `MockAdvisorClient` ([[adr-31-advisors-implementation]] regla 4) |
| `ASSISTANT_BEDROCK_MODEL_ID` | backend | dev/prod/local | no | plain task env; `.env` local | Bedrock model ID for the `assistant` **generative** tier ([[adr-35-conversational-assistant]]) — the conversational counterpart of the advisors; generates prose (temperature 0.3), so a capable model, not Nova Micro. **Must be the cross-region inference-profile form** — e.g. `us.amazon.nova-lite-v1:0`, not the bare ID (not on-demand invokable, fails `ValidationException`). Reuses `BEDROCK_REGION` — no duplicate region variable. The `boto3` + `asgiref.sync_to_async` call mechanism is owned by [[BACKEND]] ([[adr-16-async-mandatory]] rule 4), not this file. Read only outside DEBUG; DEBUG uses `MockAssistantClient` ([[adr-35-conversational-assistant]] decisión 5) |
| `WHATSAPP_TOKEN` | backend | dev/prod/local | yes | `alvs/<env>/<project>/whatsapp`; `.env` local | WhatsApp Cloud API bearer token, read only by `WhatsAppSender` outside DEBUG ([[adr-36-notifications-digest]] decisión 2); the `MockSender` reads nothing. A missing value is a `SenderError`, never a silent no-op. Sensitive — never committed |
| `WHATSAPP_PHONE_NUMBER_ID` | backend | dev/prod/local | no | `alvs/<env>/<project>/whatsapp`; `.env` local | WhatsApp Cloud API phone-number ID the `WhatsAppSender` posts messages through ([[adr-36-notifications-digest]] decisión 2). Read only outside DEBUG; DEBUG uses `MockSender` |
| `ROUTER_AUDIT_RETENTION_DAYS` | backend | dev/prod/local | no | plain task env; `.env` local | Retention window in days for `IntentQuery` audit rows ([[CHATBOT]] — Retention, closes #65); `purge_router_audit` deletes rows older than this by `created_at`. Default `30` |
| `ASSISTANT_ENABLED` | backend | dev/prod/local | no | plain task env; `.env` local | Kill switch for the page-context assistant generating tier ([[CHATBOT]], [[adr-55-page-context-assistant]]): `false` short-circuits `POST /api/assistant/ask/` before any inference call, still persisting its `AssistantQuery` audit row. Default `true`. Independent of `ROUTER_ENABLED` — the two tiers are disabled separately, because they are permanently disjoint capabilities ([[adr-15-chatbot-two-tier]] rule 1) |
| `ASSISTANT_AUDIT_RETENTION_DAYS` | backend | dev/prod/local | no | plain task env; `.env` local | Retention window in days for `AssistantQuery` audit rows ([[adr-55-page-context-assistant]] rule 6); `purge_assistant_audit` deletes rows older than this by `created_at`. Default `30`. Separate from `ROUTER_AUDIT_RETENTION_DAYS` — a different audit table with its own command |
| `ROUTER_RATE_IDLE_SKIP_SECONDS` | backend | dev/prod/local | no | plain task env; `.env` local | Idle window in seconds for the router's silent rate-abuse guard (#371, [[GLOSSARY]] router rate-abuse guard): when the requesting user's last router activity was longer ago than this, the async evaluation skips entirely — evaluates nothing. Default `20` |
| `ROUTER_RATE_THRESHOLD_PER_MINUTE` | backend | dev/prod/local | no | plain task env; `.env` local | Average messages-per-minute threshold for the router's rate-abuse guard (#371); crossing it (only checked when the idle-skip above did not apply) triggers the silent block below. Default `20` |
| `ROUTER_RATE_BLOCK_SECONDS` | backend | dev/prod/local | no | plain task env; `.env` local | Duration in seconds of the silent block the rate-abuse guard applies once triggered (#371) — every request from a blocked user returns a bare `429` with no distinguishing detail. Default `300` |

### Frontend

All frontend variables are **plain, non-secret** — task env in cloud, `.env` local.

| Name | Scope | Envs | Secret? | Source | Description |
|---|---|---|---|---|---|
| `PORT` | frontend | dev/prod/local | no | plain task env; `.env` local | Astro SSR port, 4321 ([[FRONTEND]]) |
| `HOST` | frontend | dev/prod/local | no | plain task env; `.env` local | Bind host, `0.0.0.0` |
| `NODE_ENV` | frontend | dev/prod/local | no | plain task env; `.env` local | Build/runtime mode |
| `PUBLIC_SITE_URL` | frontend | dev/prod/local | no | plain task env; `.env` local | Public site URL, client-visible |
| `PUBLIC_BACKEND_URL` | frontend | dev/prod/local | no | plain task env; `.env` local | Public backend URL, client-visible |
| `BACKEND_API_URL` | frontend | dev/prod/local | no | plain task env; `.env` local | Internal Cloud Map URL, **server-side only** ([[INFRASTRUCTURE]]) |
| `PUBLIC_PROJECT_SLUG` | frontend | dev/prod/local | no | plain task env; `.env` local | Frontend-visible copy of `PROJECT_SLUG` above ([[GLOSSARY]]) — derived, never independently set. Passed through by `compose.yaml` (locally, `${PROJECT_SLUG:-astro-drf-aws}`) and by `.github/workflows/deploy-prod.yml`'s frontend task definition (`"value": "${PROJECT_SLUG}"`), so the two names stay one source at every hop |

### Local (Compose)

Read only by `compose.yaml` ([[DOCKER]]) to publish container ports on the host — never read by application code, never present in cloud envs.

| Name | Scope | Envs | Secret? | Source | Description |
|---|---|---|---|---|---|
| `DB_PUBLISH_PORT` | compose | local | no | `.env` local | Host port publishing `db` 5432 |
| `BACKEND_PUBLISH_PORT` | compose | local | no | `.env` local | Host port publishing `backend` 8000 (reserved, stage 3) |
| `FRONTEND_PUBLISH_PORT` | compose | local | no | `.env` local | Host port publishing `frontend` 4321 (reserved, stage 3) |

## Change protocol

> [!important]
> Add the row here **first**, then use the variable. A PR that reads an undeclared variable is wrong by definition.
