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

## Startup chain (backend)

`down -v` destroys the `pgdata` volume, so the next `up` starts on an empty database. The backend's command rebuilds it before serving anything — the stack is meant to come up **usable**, which is what lets it double as a demo page:

| Step | Rebuilds |
|---|---|
| `migrate --noinput` | schema + the data migrations that fill the catalogs (`FeedType`, `Advisor`, `MarketSource`) |
| `bootstrap_admin` | the break-glass superuser, when `DJANGO_SUPERUSER_*` are set ([[adr-10-auth]] rule 8) — skipped with a log line when they are not |
| `seed_demo_operator` | one user in `ai_operators`, so the RBAC gate is exercisable ([[CHATBOT]]) |
| `seed_demo_feedlot --if-debug` | the demo domain data: clients, cattle, feed, health events, prices, ledger |
| `createcachetable` | the database-backed cache table ([[CACHE]] — no cache server, [[adr-06-cache]]) |

Then `uvicorn`. The steps are joined by `&&`, so a failure aborts the boot rather than serving from a half-built database; there is no `|| true` and adding one would hide exactly the failures this chain exists to surface.

Two properties keep the chain safe to run on **every** `up`, not only a fresh one:

- **Idempotence.** `seed_demo_feedlot` returns early when its demo clients already exist, so an `up` over a surviving volume changes nothing. Rebuilding the demo data on purpose is `--reset` (destructive), run by hand.
- **`--if-debug`.** The command refuses to run outside DEBUG, and in an `&&` chain that refusal would leave the backend down. The flag turns the refusal into a logged skip for this unattended caller only; a human typing the command outside DEBUG still gets the error. The DEBUG decision is read from `settings.DEBUG` either way — compose never re-implements Django's truthiness.

`seed_demo_feedlot` writes through the domain services, never raw INSERT, so the seeded history satisfies the same event-sourcing invariants as real data ([[BACKEND]]).

Guarded by `test_backend_startup_chain_rebuilds_the_database` in `tests/test_docker_compose.py`: losing a step leaves a stack that boots healthy and empty, which no other check would notice.

## Live reload (local dev)

Compose is **local only** ([[adr-09-docker-compose]]); production is Fargate + ECR ([[INFRASTRUCTURE]]) and never runs this file. So local has no reason to serve a production build — the `backend`/`frontend` services bind-mount their source and run **dev servers**, so a container reflects the code on disk live:

| Service | Bind | Command | Reload |
|---|---|---|---|
| `frontend` | `./frontend:/app` + anon `/app/node_modules` | `rm -f .astro/dev.json && bun run dev --host 0.0.0.0` | astro HMR |
| `backend` | `./backend:/app` + anon `/app/.venv` | `uvicorn … --reload` (via `uv run --with watchfiles`) | ASGI reload ([[adr-16-async-mandatory]]) |

- The **anonymous volume** on `node_modules` / `.venv` is load-bearing: it keeps the image's installed deps and stops the host tree from masking them. Removing it breaks startup.
- The **`rm -f .astro/dev.json`** is load-bearing too, and for the mirror-image reason: that file is *inside* the bind mount, so it is written to the host and outlives the container. `astro dev` uses it to record which PID owns port 4321; a container killed by `down` never cleans it up, and the next container resolves that PID inside its own namespace — where an unrelated process may hold the same low number — and refuses to start. Clearing it makes a rebuild deterministic. `astro dev --force`, which astro's own error message suggests, does not prevent the refusal (issue #60).
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
