# astro-drf-aws

Template. The only expected outcome is a working deploy. Owner: **kodexArg**.

- Custom AI harness + live documentation — agents enter through [AGENTS.md](AGENTS.md)
- Astro 7 (SSR) + Svelte + shadcn-svelte + Tailwind 4
- Django 6 + DRF
- Full AWS deploy via GitHub Actions (two Fargate services)
- RDS PostgreSQL + local PostgreSQL for development

## Git

| Branch | Role |
|--------|------|
| `main` | Integration (default PR target) |
| `prod` | **Production** (not `main`) |

Issues + PRs by default. Direct push to `main`/`prod`: **kodexArg only**. Labels, tags, detail: [docs/GH.md](docs/GH.md) · [adr-08](docs/adrs/adr-08-github-and-git.md).

## Local Docker

Root `compose.yaml` only ([[DOCKER]]). Profiles: `db` (Postgres only), `backend` (Django + Postgres), `full`. The `backend/` tree is a scaffolded Django 6 + DRF service with its own Dockerfile; `frontend/` (Astro SSR) is still pending and its profile is reserved.

```bash
docker compose --profile db up -d        # Postgres only
docker compose --profile backend up -d   # Django API + Postgres
python3 tests/test_docker_compose.py
python3 tests/test_docker_compose.py --smoke
```

## Where it stands

All three stages — documents & harness structure, harness construction (skills, hooks, guardian
agents), and project construction — are **done**: backend built through TDD, frontend, deploy
pipeline, and the ephemeral reference run all landed. The objective it serves is [docs/PRD.md](docs/PRD.md).

Documentation lives in [`docs/`](docs/) — Obsidian-flavored, wikilinked, one source of truth per topic. ADRs load as agent rules from [`docs/adrs/`](docs/adrs/). MIT licensed.
