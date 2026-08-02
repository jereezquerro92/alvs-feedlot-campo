---
title: adr-09-docker-compose
type: adr
category: devops
use_case: adding a Compose service or profile, choosing where backend/frontend code lives, wiring a health probe, naming a local env var
created: 2026-07-10
modified: 2026-08-02
tags: [adr, docker, local]
---

# ADR-09 — docker-compose and app paths

## CONTEXT

> Local orchestration is one root `compose.yaml`; `backend/` and `frontend/` are the only app paths it ever points at.

## ASSERTIONS

1. Reserved paths: application code for the two services will live under `backend/` and `frontend/` only. Those names are canonical ([[GLOSSARY]]). Creating alternate roots requires a new ADR.
2. Harness does not scaffold the apps. Stage 2 documents and wires Compose doctrine; Django/Astro trees are stage 3 (project construction). Agents must not invent `backend/` / `frontend/` application code unless the user asks for project construction.
3. Single Compose file: local orchestration is only repository-root `compose.yaml`. Per-app compose files are not the template default.
4. Dockerfiles will sit in `backend/` and `frontend/` when those apps exist (two images / two Fargate services — [[INFRASTRUCTURE]]).
5. Profiles: `db`, `backend`, `frontend`, `full`. Today only `db` is implemented; `backend` / `frontend` / `full` remain reserved names for when services are added to the same file.
6. No Redis in Compose ([[CACHE]]). Local DB is PostgreSQL 17 when `db` runs.
7. Env names from [[VARIABLES]]; `.env.example` is the committed local template — no secrets in git.
8. Health: db uses `pg_isready`. Backend/frontend probes (`/api/health/`, `/healthz`) apply when those services exist ([[API]], [[DOCKER]]).
9. Verification: `python3 tests/test_docker_compose.py` must pass. Optional `--smoke` exercises live `db` only until app services exist.
10. Scope: Compose is local only. Production remains Fargate + ECR ([[INFRASTRUCTURE]]).

## FORBIDDEN

- **NEVER** create application code outside `backend/`/`frontend/`, or a third app root, without a new ADR (rule 1). The two names are canonical; a third path is a stack divergence, not a convenience.
- **NEVER** scaffold Django/Astro trees before the user asks for project construction (rule 2). Stage 2 wires the doctrine; it does not invent the apps.
- **NEVER** add a per-app compose file (rule 3). `compose.yaml` at the repo root is the only orchestration file this template ships.
- **NEVER** add Redis to Compose (rule 6, [[adr-06-cache]]). The cache-server prohibition holds locally exactly as it holds in production.
- **NEVER** commit a secret into `.env.example` (rule 7). It is the local template, not a place for a real credential.

## RELATED

### related adrs

- [[docs/adrs/adr-06-cache]] — the Redis prohibition rule 6 restates locally
- [[docs/adrs/adr-03-api-and-backend]] — the health-route contract rule 8's probes must satisfy

### related files

- [[docs/DOCKER]] — the profiles, Dockerfile placement, and probe detail
- [[docs/INFRASTRUCTURE]] — the two-Fargate production shape rule 4 and rule 10 point at
- [[docs/VARIABLES]] — env names rule 7 requires
- [[docs/GLOSSARY]] — the canonical `backend`/`frontend` names
- [[docs/CACHE]] — the cache prohibition
