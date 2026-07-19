---
title: AGENTS
type: index
status: active
created: 2026-07-10
tags: [harness, index]
---

# AGENTS.md — entry point

Template: [[FRONTEND|Astro 7 SSR + Svelte]] frontend and [[BACKEND|Django 6 + DRF]] backend, two Fargate services on AWS us-east-1 ([[INFRASTRUCTURE]]). This file is an index you can trust: reach content through its links instead of re-scanning the repo.

> [!important] Read docs through the vault MCP first
> `docs/` content is reached through the **`markdown-vault-docs` MCP** — the first source of truth for any `docs/` prose or wikilink question, **before** Grep/Read ([[adr-18-markdown-vault-mcp]], [[markdown-vault-mcp]]): `search` to find, `read` to open, `get_backlinks`/`get_outlinks`/`get_similar` to traverse. Grep/Read stay correct for code, configs, and non-`docs/` files; code structure still goes to `codebase-memory-mcp` first. To go the other way — from a doc or ADR to the code it governs — consult `docs/CODEMAP.md`, the generated doc→code inverse index ([[adr-17-live-doc-backlinks]]); it is the return direction the vault graph does not draw ([[adr-17-live-doc-backlinks]] rule 6).

> [!warning] The ABC — verify before adding ANYTHING
> 1. **Does it follow [[PRD]]?**
> 2. **Does it comply with the ADRs?** (`docs/adrs/`)
> 3. **Does it modify [[API]]?**
>
> This is the ABC of every request, no matter how small. To make it possible, **[[PRD]] and [[API]] MUST be held in memory at all times**: the main session preloads both at session start, and a dispatched subagent — which `SessionStart` does not reach ([[HARNESS]]) — reads both as its first act; either way they are re-read whenever they change. No other file carries this standing requirement.

## Where the project stands

All three stages — documents, harness, project construction — are **done**. Provisioned reference-run resources are tracked in `docs/INVENTORY.md` (Phase E teardown executes from it). The objective this all serves is [[PRD]].

## The development loop

Defined in [[DEVELOPMENT-LOOP]] and given force by [[adr-07-development-flow]]; that file also carries the operational rendering — the exact sequence and the tool or skill at each step, per use case — and is opened at the start of any code. Follow it for every feature:

`idea → user-facing? → [[BDD]] → … → needs backend? → enter through [[API]]`

Inside the backend zone: confirm the existing [[API]] endpoints cannot serve the need → add the row to [[API]] → [[TDD]] flow (skills-driven) → **checkpoint: does [[API]] solve the need?** Yes returns to the frontend track; no loops back. The backend zone is entered and exited only through [[API]].

**Modifying [[PRD]], the ADRs, [[API]], or their watched surfaces means engaging the matching guardian** — `astro-drf-aws-prd` / `-adr` / `-api` — for the change, before the batch closes. Seek them when you intend to touch those files; the dispatch hook's nudge is the safety net, not the trigger. They are proactive experts, not mere gates: they triage fast, dismiss false positives in one line, and know the exact files to touch through their precise links. Verdicts and `notify` lists are binding ([[adr-11-guardians]]).

## Testing & verification

- **Smoke / end-to-end UI tests are driven through the `chrome-devtools` MCP** (chromium on the DevTools protocol at `127.0.0.1:9222`) — the DEFAULT tool for browser-level verification of the [[CHATBOT]]/chatui surface and any user-facing feature ([[BDD]], [[FRONTEND]]). Bash stands up the local stack ([[DOCKER]]) underneath it.
- **Smoke tests are ONLY allowed for the Unix user `kodex`.** They MUST NOT run under the sudo-less `pykodex` agent sandbox, nor in any headless/cron/non-interactive agent context — browser smoke is an interactive, human-`kodex`-session-only action. An agent routine that reaches a smoke-test step stops and defers to kodex.

## Index

**Product & doctrine**
- [[PRD]] — the objective and the horizon: the railguard, and growth by addition. *Always in memory.*
- [[DEVELOPMENT-LOOP]] — the canonical workflows and the tool/skill at each step; opened at the start of any code ([[adr-07-development-flow]]).
- [[GLOSSARY]] — naming authority; a term is decided here before its first use.
- [[LOCALIZATION]] — code is English, always; other languages exist only in rendered frontend output.

**Contracts (SSOTs)**
- [[API]] — the only source of valid endpoints. *Always in memory.*
- [[VARIABLES]] — the only source of environment variables; secrets live in AWS Secrets Manager, always.
- [[REQUIREMENTS]] — exact version pins; policy: latest, beta acceptable.
- [[GH]] — GitHub/git: `main` vs `prod`, issues/PRs, labels, tags, `kodexArg` only on protected lines.

**Stack**
- [[BACKEND]] — Django 6 + DRF rules; code born through TDD once the template is finished.
- [[AUTH]] — Cognito authenticates, Django authorizes; RBAC is Django Groups + DRF permissions, never Cognito ([[adr-10-auth]]).
- [[FRONTEND]] — Astro SSR + Svelte rules; bun mandatory, npm prohibited, no Node.
- [[DESIGN-SYSTEM]] — every visual and component decision; its standing decision is variable-driven theming — every visual value is a CSS custom property token, light/dark always, user-tunable on `/profile`.
- [[MELT-UI]] — the headless builder layer (Melt→Bits→shadcn); how to build a Melt component and when to choose it.
- [[HTMX]] — in the stack; Django generates fragments; Astro loads the client; sits before Svelte in the interactivity ladder.
- [[CHATBOT]] — the chat-like surface that is a **router**, not a chatbot: a closed enum, zero generation, and the permanent two-tier split that keeps choosing and generating disjoint ([[adr-15-chatbot-two-tier]]).
- [[CACHE]] — the Redis-free cache strategy; Redis is prohibited.
- [[BD]] — databases: prod, dev (cloud), local.
- [[INFRASTRUCTURE]] — the two-Fargate AWS layout, mirrored from the ALVS precedent.
- [[DOCKER]] — local Compose: root `compose.yaml`, paths `backend/` + `frontend/`, profiles. Local dev bind-mounts source and runs hot-reload dev servers — rebuild only on dependency/`Dockerfile` changes.
- M365 / Graph (capability layer) — required env only: [[VARIABLES]].

**Harness**
- [[HARNESS]] — the skills this template requires, vendored into `.claude/skills/` + `skills/`; ruled by [[adr-14-harness]]. Stack/AWS work goes through these skills, vault `.md` through `obsidian-markdown`, fan-out through `kdx-orchestrator`.

**Methodology** (the manuals ship with the template; a project creates its own entries)
- [[TDD]] — manual for `docs/tdds/`; every new backend piece is born there. The template ships no entries.
- [[BDD]] — manual for `docs/bdds/`; every user-facing feature enters there. The template ships no entries.

## Structure

- `backend/` / `frontend/` — **reserved** app paths (stage 3 project construction; not scaffolded by the harness).
- `compose.yaml` — local Docker orchestrator only ([[DOCKER]], [[adr-09-docker-compose]]); today may run `db` only.
- `docs/` — all documentation (the vault's content).
- `.claude/rules/` → `docs/adrs/` — ADRs live in the vault and load as rules through the link ([[adr-00-adr-doctrine]]).
- `docs/obsolete/` — bodies of superseded ADRs; the originals stay hollow (`status: defered`).
- `docs/CODEMAP.md` — generated doc→code inverse index, regenerated by the `kdx-live-doc` linker from its manifest; never hand-kept ([[adr-17-live-doc-backlinks]]).
- `.claude/skills/` (git-tracked, harness-loaded) mirrored by `skills/`, and `hooks/` → `.claude/hooks/` — stage 2 homes. The required skills are **vendored real copies** (self-contained, no dependence on the machine-global skill harness), inventoried in [[HARNESS]] and ruled by [[adr-14-harness]].
- `agents/` — SSOT of the guardian subagents (`astro-drf-aws-prd`/`-adr`/`-api`), reached as `.claude/agents/` and `.agents/agents/`; the hook `dispatch_guardians.py` routes watched-file changes to them.
- `CLAUDE.md` → `AGENTS.md`.
- `tests/` — harness/structure tests (e.g. Compose layout).

## Meta-rules

- ADRs state rules, never information; content lives in the referenced doc ([[adr-00-adr-doctrine]]).
- Obsidian conventions everywhere: frontmatter, `[[wikilinks]]`, callouts. One SSOT per topic — link, don't repeat.
- Git: `main` = integration, `prod` = production; only `kodexArg` pushes those lines ([[GH]], [[adr-08-github-and-git]]). Everything in code and docs is English ([[LOCALIZATION]]).

## Entra app registration (Microsoft Graph / SharePoint)

Standing choices when registering the confidential Web app that brokers app-only Graph access via `client_credentials` — not a second login IdP; Cognito still authenticates (see [[AUTH]]):

| Setting | Value | Forbidden for this use case |
|---|---|---|
| **Supported account types** | **Single tenant only** (this organizational directory only) | Multi-tenant; “any Entra + personal MSA”; personal accounts only |
| **Platform** | **Web** | SPA/public client as the token holder for the client secret |

- Env/secret names: only the three in [[VARIABLES]] (`MSGRAPH_TENANT_ID`, `MSGRAPH_CLIENT_ID`, `MSGRAPH_CLIENT_SECRET`) — app-only mode reads no others ([[adr-13-m365-graph]] rule 6). Values live in `.env` (local, gitignored) or Secrets Manager `alvs/<env>/<project>/msgraph` (cloud) — never in this file, never committed.
