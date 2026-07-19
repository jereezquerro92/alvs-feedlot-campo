---
title: DOCKER
type: reference
status: active
created: 2026-07-10
tags: [harness, docker, local]
---

# DOCKER — local containers

Local Docker doctrine for this template. Cloud layout stays in [[INFRASTRUCTURE]]. Pins in [[REQUIREMENTS]]. Env names in [[VARIABLES]]. Ruled by [[adr-09-docker-compose]].

> [!note] Stage now
> Stage 3 landed: the `backend/` and `frontend/` app trees exist and their services run from this file. Local dev **bind-mounts the source and runs dev servers with hot reload** (see [[#Live reload local dev]]) — code edits reflect with no rebuild. Run `db` alone via its profile when only Postgres is needed.

## Target layout (when apps exist)

```
backend/                 Django 6 + DRF — image build context (stage 3)
  Dockerfile
frontend/                Astro 7 SSR — image build context (stage 3)
  Dockerfile
compose.yaml             ONLY local orchestrator (repo root) — exists now
.env.example             committed local name template
```

- **One compose file at the repo root.** No per-app compose as the template default.
- **Dockerfiles will live next to each app** — same boundary as two ECR images / two Fargate services.
- Path names **`backend/`** and **`frontend/`** are canonical ([[GLOSSARY]]) even before the directories exist.

## Services

| Service | Port | Role | Profiles | Status |
|---|---|---|---|---|
| `db` | 5432 | PostgreSQL 17 | `db`, `backend`, `full` | **implemented** |
| `backend` | 8000 | ASGI Django | `backend`, `full` | **implemented**, hot reload |
| `frontend` | 4321 | Astro SSR (bun) | `frontend`, `full` | **implemented**, hot reload |

Network: single bridge `local` so future SSR can reach `backend:8000` (local stand-in for Cloud Map — [[INFRASTRUCTURE]]).

## Commands (current)

```bash
# Postgres only (available now)
docker compose --profile db up -d

# Config check
docker compose --profile db config --quiet
# also valid profile names reserved for later:
docker compose --profile full config --quiet
```

Stop / wipe: `docker compose --profile db down -v`.

When stage 3 lands, the same file grows `backend` / `frontend` services; preferred full stack becomes:

```bash
docker compose --profile full up --build
```

## Live reload (local dev)

Compose is **local only** ([[adr-09-docker-compose]]); production is Fargate + ECR ([[INFRASTRUCTURE]]) and never runs this file. So local has no reason to serve a production build — the `backend`/`frontend` services bind-mount their source and run **dev servers**, so a container reflects the code on disk live:

| Service | Bind | Command | Reload |
|---|---|---|---|
| `frontend` | `./frontend:/app` + anon `/app/node_modules` | `bun run dev --host 0.0.0.0` | astro HMR |
| `backend` | `./backend:/app` + anon `/app/.venv` | `uvicorn … --reload` (via `uv run --with watchfiles`) | ASGI reload ([[adr-16-async-mandatory]]) |

- The **anonymous volume** on `node_modules` / `.venv` is load-bearing: it keeps the image's installed deps and stops the host tree from masking them. Removing it breaks startup.
- `watchfiles` is pulled dev-only through `uv run --with watchfiles==1.2.0` — pinned in [[REQUIREMENTS]] under local-dev tooling (a used package must be pinned, [[adr-02-initial-stack]]) but excluded from the production image (`uv sync --no-dev`).

**Still needs a rebuild** (bind-mount covers code, not the image): a dependency change (`bun.lock` / `uv.lock`) or a `Dockerfile` change → `docker compose --profile full up -d --build`. An env change → `up -d` recreates, no rebuild.

**`bun run dev` is not `bun run build`.** The dev server does not catch build-time errors (e.g. a wrong import depth that breaks the production image); the `build` gate stays a separate CI step, not replaced by local hot reload.

## Environment

- Copy `.env.example` → `.env` (gitignored). Names must match [[VARIABLES]].
- Secrets never committed. Frontend will receive only non-secret / `PUBLIC_*` vars later.

## Health (when apps exist)

| Service | Probe |
|---|---|
| backend | `GET /api/health/` ([[API]]) |
| frontend | `GET /healthz` (document in app + here) |
| db | `pg_isready` (**now**) |

## Local origins

Local dev is **split-origin**: frontend `http://localhost:4321`, backend `http://localhost:8000`. There is no local ALB and no proxy service — the profile set stays as ruled ([[adr-09-docker-compose]]). In cloud both services ride one host (ALB path routing — [[INFRASTRUCTURE]]), so dev/prod are same-origin; the local divergence is bridged **by env only**: `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` ([[VARIABLES]]) carry the local origins in `.env`. Session-auth HTMX mutations work locally through that bridge, not through any proxy.

## What compose is not

- Not production deploy (Fargate + ECR — [[INFRASTRUCTURE]]).
- Not Redis ([[CACHE]]).
- Not a reason to scaffold Django/Astro early — app code is stage 3.

## Verification

```bash
python3 tests/test_docker_compose.py
```

Optional live Postgres smoke:

```bash
python3 tests/test_docker_compose.py --smoke
```
