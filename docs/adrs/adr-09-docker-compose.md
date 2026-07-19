---
title: adr-09-docker-compose
type: adr
status: active
created: 2026-07-10
tags: [adr, docker, local]
---

# ADR-09 — docker-compose and app paths

Rules only; content lives in [[DOCKER]].

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
