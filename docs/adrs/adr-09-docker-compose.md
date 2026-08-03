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

1. Application code lives under `backend/` and `frontend/` only. Those names are canonical ([[GLOSSARY]]); a third app root requires a new ADR.
2. Reserved. The apps exist; what replaced this rule is in `REJECTED`.
3. Local orchestration is the repository-root `compose.yaml` and nothing else. Per-app compose files are not part of this project.
4. Each service's Dockerfile sits in its own app path — `backend/Dockerfile`, `frontend/Dockerfile` — one image per Fargate service ([[INFRASTRUCTURE]]).
5. The profiles are `db`, `backend`, `frontend` and `full`; all four are implemented, and which services each selects is owned by [[DOCKER]].
6. The local database is PostgreSQL 17. No cache server joins it ([[adr-06-cache]] rule 1, which holds locally exactly as it holds in production).
7. `.env.example` is the committed local template and carries no secret. Env names come from [[VARIABLES]] ([[adr-51-api-and-backend]] rule 7).
8. Every service carries a health probe: `pg_isready` for `db`, `/api/health/` for the backend, `/healthz` for the frontend ([[API]], [[DOCKER]]).
9. Verification is `python3 tests/test_docker_compose.py`; its optional `--smoke` brings up `db` and asserts it healthy.
10. Compose is local only. Production is Fargate + ECR ([[INFRASTRUCTURE]]).

## FORBIDDEN

- **NEVER** create application code outside `backend/`/`frontend/`, or a third app root, without a new ADR (rule 1). A third path is a stack divergence, not a convenience.
- **NEVER** add a per-app compose file (rule 3). The root `compose.yaml` is the only orchestration file.
- **NEVER** add Redis to Compose ([[adr-06-cache]] rule 1). Local convenience is not an exception to the prohibition.
- **NEVER** commit a secret into `.env.example` (rule 7). It is the local template, not a place for a real credential.

## REJECTED

- **Compose doctrine ahead of the apps** — rules 2, 4, 5, 8 and 9 were written while `backend/` and `frontend/` held no code: rule 2 forbade scaffolding either tree outside project construction, and the rest spoke in the future tense of services that did not yet exist ("today only `db` is implemented"). Both trees, both Dockerfiles, all four profiles and all three health probes now exist, so the staging is spent and the rules state what is. It would reopen only for a fresh project spawned from this template, whose app paths start empty again.

## RELATED

### related adrs

- [[docs/adrs/adr-06-cache]] — rule 1, the cache-server prohibition rule 6 defers to
- [[docs/adrs/adr-51-api-and-backend]] — rule 7 for env names, and the health-route contract rule 8's probes satisfy

### related files

- [[docs/DOCKER]] — the profiles, Dockerfile placement and probe detail
- [[docs/constitution/INFRASTRUCTURE]] — the two-Fargate production shape rules 4 and 10 point at
- [[docs/VARIABLES]] — env names rule 7 requires
- [[docs/GLOSSARY]] — the canonical `backend`/`frontend` names
