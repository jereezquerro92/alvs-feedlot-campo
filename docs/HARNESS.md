---
title: HARNESS
type: reference
status: active
created: 2026-07-13
tags: [harness, skills, agents, ssot]
---

# HARNESS — the skills and agents this template requires

**The harness is the point of the product** ([[PRD]] — a solid harness whose railguard cannot be left, oriented to fast growth): the documentation system, the guardian and orchestrator agents, the enforcement hooks, and the **skills** vendored into the repo. This file is the SSOT for *which skills the template requires to function*, so the set is self-contained and travels with the repo instead of depending on a machine's global skill harness. Its force is [[adr-14-harness]].

## Vendoring rule

Every required skill is **vendored as a real copy** under `.claude/skills/<name>/` (git-tracked, the home the Claude harness loads) and mirrored under `skills/<name>/`. This template does **not** rely on the global symlink harness (`~/.agents/skills/`, `~/.claude/skills/`) documented for kodex's machines — a cloned repo on any machine must expose the full set with no external links. Adding or removing a required skill updates this table in the same batch ([[adr-14-harness]]).

## Required skills

| Skill | Why the template requires it | Primary consumers |
|---|---|---|
| `obsidian-markdown` | Every `docs/` file is Obsidian Flavored Markdown — frontmatter, `[[wikilinks]]`, callouts, embeds. Editing the vault correctly depends on it. | `orch-document-this`, any vault `.md` edit |
| `kdx-orchestrator` | Turns the main chat into a dispatcher over the `orch-*` workers; the multi-agent loop the template documents ([[AGENTS]]). | main loop, all `orch-*` agents |
| `kdx-triage` | Cheap go/no-go read on an idea before spending tokens; the skill `orch-evaluate` follows verbatim. | `orch-evaluate` |
| `kdx-astro-7` | Frontend stack entrypoint — Astro 7 SSR + Svelte 5 + HTMX ([[FRONTEND]], [[adr-04-frontend-and-design-system]]). | frontend work |
| `kdx-django-6-drf` | Backend stack entrypoint — Django 6 + DRF, TDD, migrations ([[BACKEND]], [[adr-03-api-and-backend]]). | backend work |
| `kdx-aws-containers` | ECS Fargate task defs / services / ECR / deploys ([[INFRASTRUCTURE]]). | deploy, infra |
| `kdx-aws-iam` | Fargate exec/task roles, GHA OIDC deploy roles ([[INFRASTRUCTURE]]). | infra, CI/CD |
| `kdx-aws-secrets-create` | Create Secrets Manager secrets `alvs/<env>/<project>/<component>` ([[VARIABLES]]). | secrets provisioning |
| `kdx-aws-secrets-manager` | Wire/rotate/audit task-definition secret injection ([[VARIABLES]]). | infra, debugging env |
| `kdx-aws-s3` | Private media buckets, presigned URLs, no CDN ([[INFRASTRUCTURE]]). | media storage |
| `kdx-aws-cost` | Cost discipline — Fargate sizing, no NAT, no Redis, single-AZ RDS ([[adr-06-cache]], [[BD]]). | spend review, blocking expensive additions |
| `kdx-aws-observability` | CloudWatch log groups, awslogs driver, ALB health ([[INFRASTRUCTURE]]). | logging, monitoring |
| `kdx-aws-cloudwatch-alarms` | Minimal alarm set — target health, 5xx, RDS storage. | alarms/SNS |
| `kdx-aws-cloudwatch-query` | Logs Insights queries over `/alvs/<project>/*`. | log search, deploy debugging |
| `kdx-aws-troubleshoot` | Diagnose failing Fargate deploys, unhealthy targets, secret injection, RDS connectivity. | incident response |
| `kdx-live-doc` | Stamps and re-syncs the [[GLOSSARY]]:live-doc block on every matched code file and regenerates `docs/CODEMAP.md`; the sanctioned path for the code→doc linking ruled by [[adr-17-live-doc-backlinks]]. Deterministic script + `manifest.json` — runnable by any tier. | any code file, `docs/CODEMAP.md` |
| `kdx-markdown-vault` | How the `markdown-vault-docs` MCP is driven — the first source of truth for `docs/` content ([[adr-18-markdown-vault-mcp]], [[markdown-vault-mcp]]): when to query it over Grep/Read, the tool cheat-sheet, the write/reindex caveat. | main loop, any `docs/` question |
| `kdx-wf-triage-and-fix` | The `triage-and-fix` Workflow — takes one issue end to end (scout → triage → route → plan → build → blind review → publish) through a deterministic JavaScript Workflow script over the `wf-*` cast. Vendored here and **not** machine-global: the cast's `tools:` grants are the enforcement, so it must travel with the repo like any other harness piece. How the party works: [[TRIAGE-TEAMMATES]]. | `Workflow({name: 'triage-and-fix'})`, the `wf-*` cast |

## Vendored MCP servers

Beyond skills, the template vendors one **MCP server** and transports it with the repo — the same self-contained rule [[adr-14-harness]] imposes on skills, applied to an MCP. Force: [[adr-18-markdown-vault-mcp]].

| Server | Why the template requires it | Transport |
|---|---|---|
| `markdown-vault-docs` | Turns `docs/` into a searchable, backlink-aware, semantically-indexed graph — the mandatory first source of truth for reaching `docs/` content ([[adr-18-markdown-vault-mcp]], [[markdown-vault-mcp]]). | Project-scoped `.mcp.json` + self-bootstrapping launcher `scripts/mvmcp.py` + git-ignored `.mvmcp/` (venv + index + embeddings). Pin in [[REQUIREMENTS]]. No machine-global registration. |

## Not vendored (intentionally)

- **`codebase-memory`** — a graph provided by the `codebase-memory-mcp` MCP server and enforced by the `SessionStart` hook; it is not a vendored skill dir. Unlike `markdown-vault-docs`, it stays **not vendored**: it is a heavy graph service shared across every project on the machine, not a per-vault index cheap to run project-local ([[adr-18-markdown-vault-mcp]] rule 4). The two are disjoint — code graph vs `docs/` graph.
  - **It is local-only.** The server is a machine-wide static binary registered in user scope, and neither the binary nor its registration travels with a clone — so it is present on kodex's machines and **absent in a Claude Code cloud session**, which carries only what the repo commits. Vendoring it is not on the table: the sandbox's GitHub proxy refuses release assets from repositories not attached to the session, whatever the network access level. Treat the graph as a local accelerator, never a dependency: away from this machine, code discovery falls back to Grep/Glob/Read with no loss of correctness, and the `graph_first` hook stays silent there rather than name a tool that isn't installed.
- **`kdx-shared-agent-context-manager`, `kdx-pc-ssh`** — incidental mentions inside `kdx-orchestrator` (a context MCP that is main-loop-only; a Cloudflare tunnel name in an example). Neither is a dependency of this template.
- The global convenience skills of kodex's machines (`kdx-report`, `kdx-handoff`, `mermaid-diagrams`, `kdx-send-to-telegram`, …) are available when present but are **not required** for the template to build, test, and deploy — so they are not vendored.

## Guardian & orchestrator agents

Agents are the other half of the harness. Their SSOT is `agents/`, reached as `.claude/agents/` and `.agents/agents/`. The three guardians (`astro-drf-aws-prd` / `-adr` / `-api`) gate [[PRD]], the ADRs, and [[API]] ([[adr-11-guardians]]); the `orch-*` workers are the orchestrator fan-out; the `wf-*` cast are the nodes of the `triage-and-fix` Workflow, resolved by `agentType` from the script and never dispatched by hand. These are not skills and are not listed above, but the harness is incomplete without them.

### Invocation shape — every agent is a subagent (decided 2026-07-18, #321)

**Standing decision: every agent under `agents/` runs as a dispatched subagent; none is an agent-team teammate, and `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is not set.** Per agent family:

- **Guardians** (`astro-drf-aws-prd` / `-adr` / `-api`) — subagents, by ruling of `astro-drf-aws-adr` (2026-07-18): the teammate mechanism's direct inter-agent mailbox is a second sibling-notification conduit, which [[adr-11-guardians]] rule 4 ("sibling notification flows only through the owner process") forbids. Subagent-only is the conforming shape; no supersession needed.
- **`orch-planner` / `orch-builder` / `orch-auditor`** — subagents: a sequential loop with a barrier at each handoff, the weak case for teams.
- **`orch-critic`, `orch-low`, `orch-changelog`, `orch-janitor`, `orch-medium`, `orch-evaluate`, `orch-document-this`, `orch-high`** — subagents: single-shot dispatch workers with no peer coordination; `orch-high` already documents "spawns subagents, not a nested team".
- **`wf-*` cast** — subagents by construction: resolved via `agentType` from the deterministic `triage-and-fix` Workflow script, never dispatched by hand.

Promoting any agent to teammate in the future is a semantic change to this decision: it re-runs the [[adr-11-guardians]] rule-4 ruling (for guardians), re-verifies the agent's definition carries no `skills:`/`mcpServers:` frontmatter (ignored by teammates), and re-sets the flag deliberately — never by leaving it on unused.

## Hook reach — SessionStart does not fire for subagents (measured 2026-07-17)

The `SessionStart` hooks — `load_ssot.py`, which preloads `docs/PRD.md` and `docs/API.md`, and, on the same gap, the `require_api_read.py` `UserPromptSubmit` nudge — fire only for the main session. A dispatched subagent's context window is built without them, so a subagent (a guardian among them) does **not** inherit the PRD/API preload. This is **measured behaviour, undocumented by Anthropic and therefore subject to change** — re-measure whenever the platform changes.

The consequence: a dispatched guardian reaches its SSOT by reading it explicitly as its first act, which each guardian definition already states. That instruction lives in the definition under `agents/` ([[adr-11-guardians]]), never duplicated into an ADR ([[adr-00-adr-doctrine]], [[adr-14-harness]]) — the file carries the content, the ADR carries only the rule.

Out of scope here: whether an agent-team teammate — itself a full session — receives the preload was pending #321 and is now moot: the standing decision above keeps every agent a subagent, so no teammate exists to measure. The question re-opens only if a future decision promotes one.
