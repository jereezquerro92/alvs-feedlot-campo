# Onboarding — astro-drf-aws (Alvsgroup)

Welcome. The objective ([PRD](docs/constitution/PRD.md)) is a **solid harness and a strongly opinionated
stack whose railguard cannot be left**, oriented to growth through new apps and features
without compromising the foundations. The harness is the point — a live documentation system
plus skills, hooks, and guardian agents; application code follows it, never the other way
around. It runs as an Astro 7 SSR frontend and a Django 6 + DRF backend, two Fargate services
on AWS us-east-1.

Owner: **`jereezquerro92`** ([docs/GH.md](docs/GH.md) is the record). AWS layout and account: [docs/constitution/INFRASTRUCTURE.md](docs/constitution/INFRASTRUCTURE.md).

## Read these two first — and keep them open

The whole project runs on a single discipline: **[docs/constitution/PRD.md](docs/constitution/PRD.md)** and
**[docs/API.md](docs/API.md)** are held in memory at all times. Read both at the start of
every session; re-read whenever they change. No other file carries this standing requirement.

Then read the entry index: **[AGENTS.md](AGENTS.md)** (= `CLAUDE.md`). It is a trustworthy
index — reach content through its wikilinks instead of re-scanning the repo.

## The ABC gate — verify before adding ANYTHING

Every change, no matter how small, passes three questions:

1. **Does it follow [PRD](docs/constitution/PRD.md)?**
2. **Does it comply with the ADRs?** (`docs/adrs/` = `.claude/rules/`)
3. **Does it modify [API](docs/API.md)?**

## How we work

- **Development loop** ([adr-07](docs/adrs/adr-07-development-flow.md)):
  `idea → user-facing? → agreed in the issue → needs backend? → enter through API`.
  The backend zone is entered and exited **only through [API.md](docs/API.md)**: an endpoint
  is valid if and only if it has a row there. Undeclared route in code = defect.
- **TDD** for every backend piece ([docs/TDD.md](docs/TDD.md), `docs/tdds/`).
- **Guardians** ([adr-03](docs/adrs/adr-03-guardians.md)) — three subagents gate the SSOTs:
  `astro-drf-aws-prd`, `astro-drf-aws-adr`, `astro-drf-aws-api`. Engage the matching guardian
  **before** touching PRD, the ADRs, or API; the dispatch hook is the safety net, not the trigger.
  Their verdicts are binding.

## The skill harness — vendored, self-contained

The **required skills travel with the repo**. They are real copies under `.claude/skills/`
(git-tracked, what the harness loads) mirrored to `skills/` — no dependence on any machine's
global skill harness, so a fresh clone works anywhere. The inventory and the "why" for each
is [docs/SKILL-INVENTORY.md](docs/SKILL-INVENTORY.md), given force by [adr-02](docs/adrs/adr-02-harness.md).

Use them as the sanctioned path, not optional aids: frontend → `kdx-astro-7`, backend →
`kdx-django-6-drf`, AWS → the `kdx-aws-*` set, vault `.md` → `obsidian-markdown`, go/no-go
triage → `kdx-triage`, multi-step fan-out → `kdx-orchestrator`. Skills **reinforce** the ABC
gate; they never waive it or a guardian verdict.

## Doctrine that will surprise you

- **No cache server, ever** — Redis/ElastiCache prohibited ([adr-06](docs/adrs/adr-06-cache.md)).
- **Cognito authenticates only; all RBAC lives in Django** (Groups + DRF permissions),
  never in Cognito claims ([adr-10](docs/adrs/adr-10-auth.md)).
- **Toolchains are fixed**: `uv` for Python, `bun` for JS (runtime + package manager).
  npm is prohibited, Node is not in the stack ([adr-50](docs/adrs/adr-50-initial-stack.md)).
- **Everything that is code is English** — always ([adr-12](docs/adrs/adr-12-glossary-and-localization.md)).
- **Secrets live in AWS Secrets Manager only**; the inventory is [docs/VARIABLES.md](docs/VARIABLES.md).
- ADRs state **rules, never information**; facts live in `docs/` and are reached by wikilink
  ([adr-00](docs/adrs/adr-00-discipline.md)).

## Git

| Branch | Role |
|--------|------|
| `main` | Integration — default PR target |
| `prod` | **Production** (never treat `main` as live) |

Issues + PRs are the default surface. Direct push to `main`/`prod`: **the owning account only** —
everyone else uses feature branches and PRs into `main`. Release tags are semver `v*`, cut from `prod`.
Detail: [docs/GH.md](docs/GH.md) · [adr-08](docs/adrs/adr-08-github-and-git.md).

## Local setup

- Backend: `backend/` (Django 6 + DRF, `uv`, ASGI on :8000). Deps in `backend/pyproject.toml`.
- Frontend: `frontend/` (Astro SSR + Svelte, `bun`) — scaffolded in stage 3.
- Local orchestration: root **`compose.yaml`** only ([adr-09](docs/adrs/adr-09-docker-compose.md)).
  Profiles `db | backend | frontend | full`; today `db` (PostgreSQL 17) is live.
  Verify layout: `python3 tests/test_docker_compose.py`.
- Copy `.env.example` → `.env` (names from [docs/VARIABLES.md](docs/VARIABLES.md); no secrets in git).

## Where we are

All three stages are done — docs, harness, and project construction.
The backend scaffold, custom user keyed on Cognito `sub`, `/accounts/` auth, RBAC, cache discipline,
and containerization all landed. The reference deploy is **prod-only and ephemeral — born dead,
user-gated on teardown** ([docs/constitution/INFRASTRUCTURE.md](docs/constitution/INFRASTRUCTURE.md)); its provisioned resources
are tracked in [docs/INVENTORY.md](docs/INVENTORY.md), from which Phase E teardown executes.

## Doc map

- **Product**: [PRD](docs/constitution/PRD.md) · [GLOSSARY](docs/GLOSSARY.md) · [LOCALIZATION](docs/constitution/LOCALIZATION.md)
- **Contracts**: [API](docs/API.md) · [VARIABLES](docs/VARIABLES.md) · [REQUIREMENTS](docs/constitution/REQUIREMENTS.md) · [GH](docs/GH.md)
- **Stack**: [BACKEND](docs/BACKEND.md) · [AUTH](docs/AUTH.md) · [FRONTEND](docs/FRONTEND.md) · [HTMX](docs/HTMX.md) · [CACHE](docs/CACHE.md) · [BD](docs/BD.md) · [INFRASTRUCTURE](docs/constitution/INFRASTRUCTURE.md) · [DOCKER](docs/DOCKER.md)
- **Method**: [TDD](docs/TDD.md)
- **Harness**: [SKILL-INVENTORY](docs/SKILL-INVENTORY.md) — required skills, vendored
- **Infra state**: [INVENTORY](docs/INVENTORY.md)
