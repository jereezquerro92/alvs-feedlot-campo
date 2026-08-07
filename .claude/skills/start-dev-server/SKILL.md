---
name: start-dev-server
description: >
  Boot the local astro-drf-aws Compose stack (Django :8000 + Astro :4321), free
  those ports first, open localhost:4321, and prove login via chrome-devtools.
  Use when the user runs /start-dev-server, asks to start local servers, bring
  up the stack, free ports 8000/4321, or open the local frontend for a session.
---

# start-dev-server

Local-only session boot for this template ([[DOCKER]], [[AUTH]], [[AGENTS]]).
Vendored under `.claude/skills/start-dev-server/` and mirrored at
`skills/start-dev-server/` ([[adr-02-harness]] rule 9). Done messages render
through the vendored `cowsay` skill — never freehand ASCII.

## Goal

- check for MCPs and Skills, you gonna need them on this session.
- closes all 8000 and 4321 open servers, doesn't matter if they aren't part of its project
- start 8000
- start 4321
- open localhost:4321
- login. This proves:
  - astro 4321
  - django 8000
  - chrome devtools

## Prerequisites (check first)

Before touching ports or Compose, verify this session has what the flow needs.
Stop and tell the user what is missing — do not improvise substitutes.

| Need | Why | How to check |
|---|---|---|
| Skill `cowsay` | Final "done" reply must go through `$SKILL_ROOT/bin/cowsay` | `.claude/skills/cowsay/bin/cowsay -l` exits 0 |
| Skill `start-dev-server` | This playbook | you are reading it |
| MCP `chrome-devtools` | Open `localhost:4321` and complete login | MCP tools available (`navigate_page` / `take_snapshot` / `click` or equivalent) |
| Chromium CDP `127.0.0.1:9222` | chrome-devtools transport ([[AGENTS]]) | port listening, or chrome-devtools can launch its own browser |
| Docker + Compose | Stack orchestration ([[DOCKER]]) | `docker compose version` |
| Repo root `compose.yaml` | Only local orchestrator ([[DOCKER]]) | cwd is the git root |
| Local `.env` | `AUTH_DEV_MODE=true`, CORS/CSRF origins for split ports ([[VARIABLES]]) | `.env` exists (from `.env.example`) |

Smoke / browser steps are **kodex-only** ([[AGENTS]]). If the Unix user is not
`kodex`, stop after starting the stack and hand the open+login proof to kodex.

Useful skills when the session continues past boot: `kdx-django-6-drf`,
`kdx-astro-7`, `kdx-markdown-vault`. They are not required to complete this
skill's Goal.

## Procedure

Copy and track:

```
start-dev-server:
- [ ] 1. Prerequisites OK (MCPs + Skills + Docker + .env)
- [ ] 2. Free ports 8000 and 4321 (host-wide)
- [ ] 3. Start Compose profile `full` (db + backend:8000 + frontend:4321)
- [ ] 4. Wait until both health probes pass
- [ ] 5. Open http://localhost:4321 via chrome-devtools
- [ ] 6. Login (dev path) — proves Astro + Django + chrome-devtools
- [ ] 7. Announce done through vendored cowsay
```

### 1. Prerequisites

Run the table above. Fail closed if `chrome-devtools` or `cowsay` is missing.

### 2. Free ports 8000 and 4321 (host-wide)

Kill **any** listeners on those ports — Compose from this repo, another
checkout, a host uvicorn/astro, anything. Then bring this project's stack down
so the next `up` is clean.

```bash
# From repo root
bash .claude/skills/start-dev-server/scripts/free-ports.sh
docker compose --profile full down --remove-orphans
```

`free-ports.sh` must succeed (or report nothing was bound) before continuing.
Do not skip it because "those ports are probably free."

### 3–4. Start 8000 and 4321

```bash
docker compose --profile full up -d --build
bash .claude/skills/start-dev-server/scripts/wait-healthy.sh
```

- Backend health: `GET http://127.0.0.1:8000/api/health/` ([[API]])
- Frontend health: `GET http://127.0.0.1:4321/healthz` ([[FRONTEND]])

Rebuild only when deps/`Dockerfile` changed is fine; `--build` is safe for
this boot skill. Hot-reload bind-mounts apply after the containers are up
([[DOCKER]]).

### 5. Open localhost:4321

Via **chrome-devtools** MCP only (not a raw `xdg-open` as the proof path):

1. `navigate_page` / `new_page` → `http://localhost:4321/`
2. `take_snapshot` — page must render (Astro SSR alive)

### 6. Login (proof)

Local Cognito-free path ([[AUTH]], [[API]] `GET /accounts/dev-login/`):

1. From the frontend snapshot, click the login control that points at
   `${PUBLIC_BACKEND_URL}/accounts/login/` (usually `http://localhost:8000/accounts/login/`),
   **or** navigate directly to
   `http://localhost:8000/accounts/dev-login/?email=dev@example.com`
2. Expect redirect back to `http://localhost:4321/` with a session
3. Snapshot again — UI must show an authenticated state (not the anonymous
   login CTA)

That single flow proves:

| Layer | Evidence |
|---|---|
| Astro `:4321` | Frontend rendered and accepted the post-login redirect |
| Django `:8000` | `/accounts/login/` → `/accounts/dev-login/` opened the session |
| chrome-devtools | Navigation, snapshot, and click/fill all worked |

Default allowlist identity: `dev@example.com` ([[VARIABLES]]
`AUTH_BOOTSTRAP_ALLOWLIST`).

### 7. Done — cowsay only

Write the completion message in **English**. Pipe it through the vendored
binary (never freehand the cow or the balloon):

```bash
SKILL_ROOT="$(git rev-parse --show-toplevel)/.claude/skills/cowsay"
"$SKILL_ROOT/bin/cowsay" <<'COWEOF'
start-dev-server done.
:8000 Django healthy. :4321 Astro healthy.
Opened localhost:4321 and completed dev-login via chrome-devtools.
COWEOF
```

User-visible final reply = that stdout only (one fenced code block), per the
`cowsay` skill.

## Failure rules

- Port free failed → stop; report PIDs/`ss` output; do not start Compose on a
  conflicted host.
- Health wait timed out → `docker compose --profile full ps` + recent logs;
  do not claim done.
- chrome-devtools missing or CDP down → stack may be up, but the Goal is
  incomplete; say so in plain text (no fake cow).
- Login did not land authenticated → Goal incomplete; do not cowsay success.

## Out of scope

- Cloud / Fargate deploys ([[INFRASTRUCTURE]])
- Production Cognito login
- Running the full pytest / bun suites (optional after boot, separate ask)
- Non-`kodex` browser smoke ([[AGENTS]])
