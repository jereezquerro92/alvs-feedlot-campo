---
title: REQUIREMENTS
type: reference
status: active
created: 2026-07-10
tags: [harness, requirements, versions]
---

# REQUIREMENTS

Exact version pins for the template. Policy: **latest available, beta acceptable** (owner's explicit decision). All versions re-verified against PyPI / npm / official sources on **2026-07-11** (A1 re-pin sweep).

Stack context: backend rules → [[BACKEND]], frontend rules → [[FRONTEND]], database → [[BD]], full product scope → [[PRD]].

Frontend toolchain is **bun** — package manager AND runtime; npm is prohibited and Node is not in the stack (Node 24 LTS is recorded only as a documented fallback). Redis is prohibited ([[CACHE]]). Ruled by [[adr-02-initial-stack]].

## Backend (Python)

| Package | Version | Status | Note (checked 2026-07-11) |
|---|---|---|---|
| Django | 6.0.7 | stable | **Fallback taken (A1, 2026-07-11):** DRF 3.17.1 still omits `Framework :: Django :: 6.1` from its classifiers, so the pre-decided fallback rule applies and Django is pinned to **6.0.7 stable** (also the current PyPI latest; 6.1 final expected ~Aug 2026). Re-evaluate when DRF declares 6.1. |
| djangorestframework | 3.17.1 | stable | Latest. Classifiers list Django up to **6.0** only; 6.1 **not** present (re-checked 2026-07-11) — this is why Django is held at 6.0.7. Flag clears once a DRF release adds the 6.1 classifier. |
| Python | 3.14.6 | stable | |
| psycopg | 3.3.4 | stable | PostgreSQL driver ([[BD]]) |
| uvicorn | 0.51.0 | stable | **Chosen ASGI server** (decided 2026-07-10): standalone with `--workers`, sized by `UVICORN_WORKERS` (default `4`, [[VARIABLES]]) in the `backend/Dockerfile` CMD (closes #262). Async-first — AI/streaming features expected soon ([[BACKEND]]). gunicorn evaluated and not selected; it is not in the stack. |
| drf-spectacular | 0.30.0 | stable | OpenAPI schema ([[API]]) |
| django-cors-headers | 4.9.0 | stable | |
| PyJWT | 2.10.1 | stable | Live Cognito ID-token verification (RS256/JWKS) at the `/accounts/callback/` seam ([[AUTH]]). Installed with the `[crypto]` extra (pulls `cryptography`) for RS256. Added 2026-07-12. |
| uv | 0.11.28 | stable | Python toolchain — not pip |
| msal | 1.37.0 | stable | Microsoft Graph delegated OAuth/refresh-token acquisition ([[adr-13-m365-graph]]). Added 2026-07-12. |
| httpx | 0.28.1 | stable | Thin HTTP client for Graph REST v1.0 calls ([[adr-13-m365-graph]]). Added 2026-07-12. |
| boto3 | 1.40.15 | stable | **Runtime dependency (flipped 2026-07-14, closes #96):** Bedrock inference calls for the chatbot `router` choosing tier, wrapped in `asgiref.sync_to_async` — never `aiobotocore` ([[adr-16-async-mandatory]] rule 4, [[BACKEND]]). Still also used test-side by the `cognito_live` integration test ([[AUTH]]). |
| whitenoise | 6.12.0 | stable | In-process static-file serving for `/admin/` and the DRF browsable API — no CDN, no S3 media, admin-only low-volume statics ([[BACKEND]]). Checked 2026-07-16, closes #254. |

## Backend — dev/test (not shipped in the image)

Dev/test-only dependencies for the [[TDD]] T2 flow (`uv run pytest`) and the `kdx-django-6-drf` skill. Installed in a **`dev` dependency group** (`uv` dev group), **excluded from the production container image** — never a runtime dependency. Ruled by [[adr-02-initial-stack]] (a used package must be pinned).

| Package | Version | Status | Note (checked 2026-07-11) |
|---|---|---|---|
| pytest | 9.1.1 | stable | Test runner — the T2 gate is `uv run pytest` ([[TDD]]) |
| pytest-django | 4.12.0 | stable | Django integration for pytest (`@pytest.mark.django_db`, settings wiring) |
| factory_boy | 3.3.3 | stable | Model factories for fixtures — the skill/[[BACKEND]] prefer factories over large fixtures. Package name on PyPI is `factory-boy`. Classifiers list Django up to 5.1 (test-only, works with 6.x by model introspection); re-check when it declares 6.x. |

## Backend — local-dev tooling (`uv run --with`, not shipped)

Pulled ephemerally by a `compose.yaml` dev command through `uv run --with` — not in the `dev` group, never in the production image (`uv sync --no-dev`). Ruled by [[adr-02-initial-stack]] (a used package must be pinned): the pin lives both here and in the `--with` invocation. Local Compose hot reload is owned by [[DOCKER]].

| Package | Version | Status | Note (checked 2026-07-16) |
|---|---|---|---|
| watchfiles | 1.2.0 | stable | Reload signal for `uvicorn --reload` in the local `backend` dev server ([[DOCKER]], [[adr-16-async-mandatory]]). Pinned in `compose.yaml` as `--with watchfiles==1.2.0`. Added 2026-07-16. |

## Frontend (bun)

| Package | Version | Status | Note (checked 2026-07-11) |
|---|---|---|---|
| Astro | 7.0.7 | stable | Astro 7 is the current major. The `beta`/`rc` npm dist-tags are **stale** — nothing newer than 7.0.7 exists. |
| Svelte | 5.56.4 | stable | |
| @astrojs/svelte | 9.0.1 | stable | |
| @astrojs/node | 11.0.2 | stable | Standalone SSR adapter, executed under bun ([[FRONTEND]]) |
| tailwindcss | 4.3.2 | stable | Tailwind 4, CSS-first config; `@tailwindcss/vite` same version |
| shadcn-svelte | 1.4.1 | stable | CLI that vendors components into the repo ([[FRONTEND]]) |
| bun | latest | stable | Package manager AND runtime; npm prohibited; Node dropped (Node 24 LTS = documented fallback only) |
| htmx.org | 2.0.10 | stable | HTMX 2 client library via bun ([[HTMX]]). Package name on the registry is `htmx.org`. |
| melt | ^0.44.0 | active | headless builder layer under Bits UI/shadcn-svelte ([[MELT-UI]], [[adr-04-frontend-and-design-system]]). Added 2026-07-14. |
| @happy-dom/global-registrator | 20.10.6 | stable | dev-only. Registers a DOM into the `bun test` global scope so a component can be mounted client-side — the harness enforcing [[adr-22-showcase-ready-components]] rule 1. Never shipped in the frontend image ([[FRONTEND]]). Added 2026-07-16. |
| @astrojs/check | 0.9.9 | stable | dev-only. Backs the `bun run check` (`astro check`) typecheck gate; pinned so a fresh clone runs it non-interactively instead of hitting astro's auto-install prompt. Never shipped in the frontend image ([[FRONTEND]]). Latest confirmed 2026-07-17 (checked 2026-07-17). Added 2026-07-17. |
| typescript | 6.0.3 | stable | dev-only. Peer required by `@astrojs/check`; its peer range `^5.0.0 || ^6.0.0` excludes the registry-latest 7.0.2, so 6.0.3 is the latest satisfying version ([[adr-02-initial-stack]] rules 1–2). Never shipped in the frontend image ([[FRONTEND]]). Latest 6.x confirmed 2026-07-17 (checked 2026-07-17). Added 2026-07-17. |

## Database

| Package | Version | Status | Note |
|---|---|---|---|
| PostgreSQL | 17.9 | stable | RDS + local, same version ([[BD]]). Latest 17.x confirmed 2026-07-11. |

## Harness tooling (MCP)

Not shipped in any container — a **dev-harness** dependency, installed into a project-local venv under `.mvmcp/.venv` by `scripts/mvmcp.py`, never on a Fargate task. Ruled by [[adr-18-markdown-vault-mcp]]; usage in [[markdown-vault-mcp]].

| Package | Version | Status | Note (checked 2026-07-14) |
|---|---|---|---|
| markdown-vault-mcp | 3.0.4 | stable | The vendored `markdown-vault-docs` MCP over `docs/` ([[adr-18-markdown-vault-mcp]], [[HARNESS]]). Two install shapes at this one version, selected per environment ([[markdown-vault-mcp]]: vault MCP profile): the `full` profile adds the `[embeddings]` extra (pulls `fastembed`) for local semantic search — no API key, no external service, model `BAAI/bge-small-en-v1.5`; the `keyword` profile installs the plain package, where `fastembed`'s model host is unreachable. The extra is not a second pin — the version is identical either way. Added 2026-07-14. |

## Re-pin rule

> [!note]
> Each re-pin re-runs the same policy — **latest available, beta acceptable** — and updates this table with the date checked. Current check date: **2026-07-11** (A1 sweep: all pins re-verified; only Django changed — 6.1b1 → 6.0.7 stable via the DRF-classifier fallback). Never bump a pin without recording the new check date in the Note column.
