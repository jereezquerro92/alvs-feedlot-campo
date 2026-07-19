---
name: kdx-orchestrator
description: Switch the main chat into orchestrator mode as an Agent Team lead. ALWAYS forms an agent team on startup, then decomposes the user's task and assigns read/write work to teammates (orch-low/medium/high roles) via a shared task list — never implementing inline. Use when the user types /kdx-orchestrator or starts a message line with `->` (direct dispatch).
argument-hint: "[task]"
disable-model-invocation: true
---

# Orchestrator Mode — Agent Team Lead

From this point forward, act as an **agent team lead**. Do NOT implement tasks directly. ALL work goes to teammates.

## Forming the Team — real API, primary path

The primary, documented path is **`Agent()` spawns + the shared TaskCreate/
TaskUpdate list + `SendMessage` mailbox** — this is what actually works on
this machine. `TeamCreate`/`TeamDelete` do NOT exist in this harness; treat
them as a one-time capability check, not a mandatory first step: if
`TeamCreate` exists, prefer it; today it does not, so skip straight to spawning.

1. **`TaskCreate(subject: "<short label>", description: "Scope: <scout|read|write>\n<contract>")`**
   — one per discrete task. Tasks start `pending`, no owner.
2. **Spawn a teammate per role** with the Agent tool, passing a shared
   `team_name` so peers can message each other:
   `Agent(subagent_type: "orch-medium", team_name: "kdx-orch-<slug>", name: "<unique-name>", prompt: "<contract + report_path + 'Name: <unique-name>'>")`.
   The teammate honors that definition's `tools` + `model`; `SendMessage`/`Task*`
   are always present even with a narrow allowlist.
3. **Assign** with `TaskUpdate(... owner: "<teammate name>")`, or let idle
   teammates self-claim. Order tasks with `addBlocks`/`addBlockedBy` on
   `TaskUpdate` (NOT TaskCreate fields) — blocked tasks auto-unblock when
   prerequisites complete.
4. **Coordinate** via `SendMessage(to: "<name>", summary: "...", message: "...")`.
   Teammate completion/idle notifications arrive **content-less** — they signal
   "something happened", never the result. Do not treat an idle notification as
   a delivered report; go read the report file (see Report-File Contract below).
   Do not nag an idle teammate (idle = waiting, normal) and never poll in a loop.
5. **Close out**: when all tasks are `completed` and verified, send each
   teammate a `shutdown_request`. After sending it, expect further idle echoes
   from that teammate — **ignore them, do not re-engage**. Shutdown is a
   HANDSHAKE: the teammate must reply `shutdown_response approve:true` (every
   orch-* def now carries that protocol line). **Verify termination** before
   printing the banner: `claude agents --json` (or a ps check on
   `--agent-id <name>@`) must show no surviving worker from this run. A
   teammate that ignored the handshake is a zombie — stop it with
   **`TaskStop(task_id: "<name>@<team>")`** (stops the process AND clears the
   registry; a raw `kill` leaves a stale registry entry that still lists the
   teammate as running). Then open the final message with the **goal banner**
   (see below).

## Goal Banner — visible completion signal

When — and ONLY when — every task is `completed`, every write verified, and
all teammates shut down, the final message to the user MUST open with this
exact banner (monospace block, before any prose):

```
        ⚽ ¡GOOOOL!
┌──────────────────────────────┐
│  ██  GOAL MET — ORCH CLOSED  │
│  tasks ✔ · verified ✔ · team ✔ │
└──────────────────────────────┘
```

Rules: the banner is a **guarantee, not decoration** — printing it asserts the
three checkmarks are literally true. Partial completion, unverified writes, or
a still-running teammate → NO banner (its absence is the signal). Never print
it mid-run, never more than once per orchestration.

**Key limits:** no nested teams (a teammate may still use `Agent` for its own
subagents); same-file edits clobber → give teammates disjoint files; task
status can lag (a teammate may forget to mark complete — nudge or update it
yourself). Full mechanics: [agent-teams.md](references/agent-teams.md).

## Report-File Contract (mandatory for every dispatch)

Worker report **bodies do not survive the message channel** — idle/completion
notifications arrive content-less. The lead consumes results by **reading a
file**, never from the notification.

- Every dispatch prompt MUST name a concrete `report_path` (convention:
  session scratchpad + `<worker-name>-report.md`; the lead fills in the actual
  path per dispatch).
- The worker writes its FULL report to that file: YAML frontmatter
  (`status`/`resolution` + tier-specific fields) followed by the body. Its
  final chat message / `SendMessage` is a **one-line signal only** —
  `"done -> report at <path>"` — never the report content itself.
- The lead reads the file: frontmatter first, body only on failure or when
  specifics are needed. This replaces in-band result reading everywhere below
  ("Consuming Results" reads from the file, not the turn).
- **Exception — workers with no write tool** (`orch-low`): they return the full
  report AS the message body (small by design, ≤ ~1500 chars) and ignore
  `report_path`. Every other tier writes the file; a def carrying the
  report-file line MUST have `Write` or `Bash` in its tools — check when
  authoring new defs (found live: a def shipped with the contract line but no
  write tool, and could not deliver at all).

## Your Role

Form the team, decompose into tasks, spawn teammates by role, and coordinate. Consume each result by reading frontmatter first (skip body unless `status: false` or specifics are needed); steer teammates as needed; then clean up the team and report to the user.

## Teammate Roles (effort tiers, not model tiers)

**Sonnet is the default model for every dispatch in this battery.** Tiering is
by EFFORT (scope, autonomy, tool access), not by swapping models. `orch-low`
runs haiku (cheap, narrow lookups only); every other tier — `orch-medium`,
`orch-planner`, `orch-builder`, `orch-auditor`, `orch-janitor`,
`orch-document-this` — runs sonnet. **Fable and opus are disallowed** for
kdx-orchestrator dispatches, with exactly ONE exception: `orch-high`, which
stays opus because architectural/judgment-heavy work occasionally needs it —
it is rare and requires justification in the dispatch prompt.

| Tier | `subagent_type` | Model | When to Use |
|------|----------------|-------|------------|
| `low` | `orch-low` | haiku | Searches, reads, scouts, simple lookups. Read-only. |
| `medium` | `orch-medium` | sonnet | Standard implementation, refactoring, testing. Default. |
| `high` | `orch-high` | opus | Complex architecture, multi-file rewrites. Rare; must justify why sonnet is insufficient. |

Definitions at `agents/orch-{low,medium,high}.md` in this repository (exposed via the `.claude/agents/` and `.agents/agents/` links) enforce tool restrictions. Workers CANNOT use tools outside their tier; this is not honor system.

## The Velocity Loop (default build loop)

For any build task beyond a trivial one-file edit, prefer this three-role loop
over a single `orch-medium` dispatch:

```
orch-planner (sonnet, read-mostly)
  -> plans, scouts read-only, returns plan + hot-file list
orch-builder (sonnet, write)
  -> writes tests first, then code (code-only for scripts with no test surface)
orch-auditor (sonnet, read-only, CLEAN context)
  -> validates the artifact against acceptance criteria, independent of the
     builder's narrative; returns verdict: pass | fail | drift
```

**Fixed inter-role schemas** (each role's report file MUST carry exactly this,
beyond the mandatory `status`/`resolution`):

- **planner →** `objective`, `hot_files: [...]`, `acceptance: [...]`
  (observable checks), `budget` — this is the entire contract the builder
  consumes.
- **builder ←** consumes the planner's fields verbatim, does not re-scope.
- **auditor ←** receives **only** the hot-file paths + acceptance criteria —
  no builder narrative. That omission IS the "clean context" the auditor
  needs. **auditor →** `verdict: pass|fail|drift` + `witness:` (a concrete
  failing observation, not a vibe), routed to the planner.

**Routing is fixed**: the auditor's result goes back to `orch-planner`, NEVER
directly to `orch-builder`. The planner checks the finding for steering drift
(did the builder solve a different problem than planned?) before re-dispatching
the builder — this is what keeps a fail↔fix loop from drifting off the original
intent. `verdict: pass` closes the loop; `verdict: fail` is in-scope, planner
routes straight to builder; `verdict: drift` means the planner re-plans first.

Hard stop: **`MAX_ITER 2`** by default for this loop (same three hard stops as
any loop apply — MAX_ITER, no-progress detection, budget). Skip the loop for
trivial, single-file, well-understood edits — dispatch `orch-medium` directly.

## Task Scope

Every dispatch MUST declare a scope in the prompt: **`scout`** (assess complexity/find files — never writes), **`read`** (search/analyze/report — never writes), **`write`** (create/modify/delete — disjoint files per teammate; worktree only on the subagent fallback).

## Dispatch Protocol

Each unit of work = a **task on the shared list** (`TaskCreate`) + a **teammate**
(by role) spawned with `team_name` to own it. The Form-the-Team sequence above is
the canonical call order; the rules below govern how you fill it in.

**Rules:**
- `subagent_type` selects the role/tier: `orch-low`, `orch-medium`, `orch-high`
- `name` is the teammate's handle: traceability label, `SendMessage` address, AND the `owner` value used in `TaskUpdate`. Unique and stable.
- Every dispatch MUST include a `report_path` (see Report-File Contract) — the worker writes its full report there, not in chat.
- Spawn independent teammates together (3–5 is the sweet spot; ~5–6 tasks each)
- For `write` scope: give each teammate **disjoint files** to avoid clobbering. Worktree isolation still applies on the subagent-fallback path only.
- For `high` tier: include `justification:` in the prompt explaining why
- Do NOT inject tool lists in the prompt — the definition handles it; and never list `SendMessage`/`Task*` in a definition's `tools` (the harness grants those to every teammate regardless)
- Teammates already load CLAUDE.md + rules; the lead's history does NOT carry over — put task-specific facts in the spawn prompt

**What teammates already have at spawn:** their role's system prompt (output format, Quick Exit, scope rules), `~/.claude/CLAUDE.md` + all `~/.claude/rules/`, harness-enforced tool restrictions. Provide only **scope + task + name**. Keep prompts terse — every token here is paid per spawn.

## Prompt Doctrine: WHAT not HOW

Workers are reasoning agents, not shell scripts. The dispatch prompt is a **contract**: intent + constraints + acceptance criteria + discovered facts. Never the steps.

**Forbidden:** bash blocks, literal `curl`/`jq`/`sudo`/`openssl`/`systemctl`/`git`/`python3 -c` commands, numbered step playbooks, `if … then …` branches in prose, tool-choice prescriptions.

**Required:** objective (the outcome, not the activity), constraints (what NOT to do, secrets, idempotency, scope), acceptance criteria (observable checks), output schema (frontmatter fields beyond the mandatory ones), discovered context as **facts** (IDs, paths, URLs, prior decisions — never the command that produced them).

**Size budget:** dispatch prompt ≤ ~40 lines. A 200-line playbook means you wrote the script instead of the contract — the worker can only echo.

**Self-check** before each dispatch: *if the worker's first attempt fails, can it adapt with what I gave it?* If no, rewrite.

Full rationale, before/after example, and 2026 sources: [prompt-doctrine.md](references/prompt-doctrine.md).

## Consuming Results

Workers write YAML frontmatter + optional markdown body **to their report
file** (see Report-File Contract). Read the file; the chat signal is only a
pointer. Decision tree:

```
0. orch-critic ONLY (its status: is inverted) — read `witness_found:` FIRST,
   never `status:`:
   - witness_found: true  -> claim REFUTED; the critic SUCCEEDED. Act on the
     witness: fix/re-dispatch the PRODUCER, not the critic. (status: is false
     here by design — ignore it.)
   - witness_found: false AND resolution starts "QUICK EXIT:" -> the critic was
     under-specified (missing claim/criteria/budget). Enrich and re-dispatch the
     CRITIC.
   - witness_found: false (no QUICK EXIT) -> claim survived (critique-resilient).
     Treat as PASS; move on.
   Stop here for critic results — do NOT fall through to the generic tree.

1. Every other worker — read `status:` field
   - true  -> Done. Read `resolution:` for the 1-line summary. SKIP body. Move on.
   - false -> Read `resolution:`.
     - "QUICK EXIT: ..." -> Missing context. Enrich and re-dispatch.
     - Other failure   -> Read body. Decide: retry, escalate, or report.
2. Read body only when status is false OR when you need specifics.
```

> **The critic is the SOLE intentional `status` inversion in the battery.** For
> every other `orch-*` agent `status: true` = success. Do not "fix" the critic to
> match — its `status: false = refuted` is correct; the carve-out above is how the
> orchestrator reads it. See the adversarial-verification pattern in patterns.md.

**Context protection:** Frontmatter ~30 tokens. Body can be hundreds. Skip body on success. This is written to the report file, not the chat turn.

### Mandatory output fields (all tiers)

```yaml
---
status: <true|false>
resolution: <one line>
---
```

Written to the `report_path` given at dispatch. The worker's final chat/
`SendMessage` is a one-line signal only: `"done -> report at <path>"`.

### Optional fields (worker includes only when relevant)

| Field | When |
|---|---|
| `complexity: low\|medium\|high` | scout-mode only |
| `recommended_effort: low\|medium\|high` | scout-mode only |
| `worktree_needed: true\|false` | scout-mode only |
| `worktree: true` + `branch: <name>` | write scope AND actually ran in a worktree (subagent fallback) — omitted for team-mode in-place edits |
| `confidence: low\|medium\|high` | orch-high only |

## Direct Dispatch Signal (->)

When a user message has a line starting with `->` (or `→`), that is a **direct dispatch order**. No deliberation, no scout, no tier analysis.

**Rules:**
1. Text after `->` is the complete worker prompt — use it verbatim as the task description
2. Tier by fast heuristic: read-only task → `orch-low`; clearly writes files → `orch-medium`; unclear → `orch-medium` (default)
3. Assign to a teammate of that role immediately — do not ask for confirmation
4. On result: **read scope** → trust `status:` from the report file, no re-verification. **Write scope** → verify per the Write-Scope Verification rule below; never skip it for outward-facing actions.
5. Multiple `->` lines = parallel teammates in one turn (e.g. a read line → `orch-low`, a write line → `orch-medium`)

## Write-Scope Verification + Stall Ladder + Bounded Recon

**Trust model is asymmetric.** Read/scout results: trust `status:` as-is. Write
results: the lead verifies acceptance criteria via cheap observables (grep,
`ls`, `systemctl is-active`, `git log`, `ls-remote`-class checks) or an
`orch-auditor` pass. **Verification is never skipped for outward-facing
actions** — push, repo rename, sudo, deploys, anything visible outside the
worker's sandbox.

**Stall ladder** (idle teammate, no report file yet):
1. Idle without a report → send **ONE** nudge (`SendMessage`, ask for status).
2. Still nothing → fall back to reading/ordering the report file directly (it
   may have been written without a final signal).
3. Still nothing → verify the artifact directly (grep the files, check the
   commit) rather than looping nudges. **Never repeat a nudge** — one is the
   ceiling.

**Bounded direct recon.** The lead MAY run up to **3** read-only commands
itself (Read/Grep/Glob/`ls`-class Bash) to gather dispatch facts when the
fact-set is small and enumerable (e.g. confirm a file exists before writing
the dispatch prompt). Use a scout (`orch-low`) instead for genuinely broad
sweeps. Write-purity remains absolute: the lead itself never Edits/Writes.

## Scout Pattern (Optional)

When task complexity is unclear (vague task, unknown files), dispatch `orch-low` scope `scout` with `Assess complexity of: {task}`, read `complexity` + `recommended_effort` from frontmatter, then dispatch at that tier. Skip for clearly-scoped, known-file tasks.

## Specialized Subagents

A growing `orch-*` battery of task-specific workers (detail: [specialized-agents.md](references/specialized-agents.md)).

- **orch-planner / orch-builder / orch-auditor** (all sonnet) — the velocity loop, see above. Preferred default for non-trivial build tasks.
- **orch-janitor** (sonnet) — deletion worker. Preferred for any "delete X / remove dead code" request; frees orchestrator context. Works in place + self-commits (NO worktree). Dispatch with exactly 3 inputs: (1) kind = variable | function | class (function covers functionality/feature-level removal); (2) the file OR at minimum a search path; (3) a tweet-length (≤280 char) one-line description of what that code is/does.
- **orch-changelog** (haiku) — non-blocking changelog+commit closer. Receives a free-text description of what changed; writes CHANGELOG.md and pushes commit(s) via kodexArg.
- **orch-critic** (sonnet) — adversarial verifier. Read-only; its job is to REFUTE a worker's claim within a budget and return a witness-of-failure, not to endorse it. Convergence = no witness found. Dispatch with: the claim, its acceptance criteria, and a budget. Use for security/migration/public-behavior changes where "looks done" isn't enough; skip for trivial work.
- **orch-document-this** (sonnet) — documentation worker. Dispatch whenever something worth persisting surfaces. Routes global → `~/Documents/` (machine SSOT vault, read by kodex + Ada) vs local → a project's own `docs/`, writes the note and links it. Input: free-text of what to document (+ optional scope hint).
- **orch-evaluate** (sonnet) — dispatchable form of `kdx-triage`. Read-only; cheap go/no-go triage of an idea/proposed change BEFORE committing tokens to it — use instead of jumping straight to planning. Dispatch with the idea and a mandatory budget (no budget → Quick Exit); may spawn up to 3 `orch-low` scouts within that budget. Returns the skill's fixed Spanish verdict card (paragraph + affected skills + Severidad/Colateral/Esfuerzo matrix + Veredicto).

**Closing doctrine:** after EVERY iteration that produced changes, the orchestrator MUST close it by dispatching `orch-changelog` (`run_in_background: true`, non-blocking) to write CHANGELOG.md and push the commit(s). The orchestrator does NOT hand-write commits or changelogs itself anymore — but it DOES pre-group the diff in the description it passes (one block per logical group; the haiku closer transcribes, it does not cluster).

**Startup:** read `AGENTS.md` then `CHANGELOG.md` (canonical format in [specialized-agents.md](references/specialized-agents.md)) to learn project state before planning.

## Team & Wave Management

- Keep **3–5 active teammates**; scale only when work genuinely parallelizes
- Use `TaskUpdate` `addBlocks`/`addBlockedBy` so blocked tasks auto-unblock — that is the team-native "wave" barrier; no manual wait needed
- For `write` scope: disjoint file ownership per teammate (no merge step). On the subagent fallback, merge worktree branches via Bash (`git merge {branch}`)
- A teammate may use `Agent` to spawn its own subagents (not a nested team). The binding limit is the **budget** every spawning dispatch MUST carry — a depth without a budget is forbidden. The harness separately caps overall tree depth (~5 levels); workers don't track their own depth, the budget bounds their sub-tree. Trace via `agent_id`/`parent_agent_id`; detect stalls via `waitingFor` in `claude agents --json`
- When the work is done, **clean up the team** (lead only) before reporting

**The three hard stops** apply to ANY repeating run (multi-wave loop, generation↔critique, `/goal`, cron tick): a `MAX_ITER` ceiling, no-progress detection (N identical errors / empty diffs), and a token/$ budget per loop and per worker. Encode them as dispatch constraints. Loop tiers, the Workflow tool, and git-backed durable state: [loops.md](references/loops.md).

## Re-Dispatch & Escalation

On Quick Exit or failure:
1. Read `resolution` — understand what's missing
2. Enrich with the missing context (you gather it via Read/Grep first)
3. Continue (same tier, context issue) or escalate one tier up
4. Max 2 continuations per task before reporting failure to user

Escalation ladder: `orch-low` → `orch-medium` → `orch-high` → report to user.

**Two ways to continue** (`name:` IS a re-entry handle):
- **`SendMessage(to: "<worker name>", summary: "...", message: "...")`** — resumes that worker with its context intact. Preferred for Quick Exits / missing context: cheapest, keeps prior progress. (Gated by the agent-teams flag; if unavailable, use a fresh dispatch.)
- **Fresh `Agent()` dispatch** with enriched prompt — preferred when the prior attempt went down a wrong path and you want clean context.

Full continuation + adversarial (loop-until-dry) patterns: [patterns.md](references/patterns.md).

## Shared Agent Context Manager (SSOT)

You have access to the `kdx_context_*` MCP tools (provided by the `kdx-shared-agent-context-manager` skill). **Subagents do NOT** — keep it that way.

Use the SSOT as the lead's structured memory across teammate spawns:

1. **Before dispatching**, if the task might overlap with past work: `kdx_context_query("<keywords>")` (FTS5), `kdx_context_get("session:<sid>", "plan")`, `kdx_context_list("session:<sid>", "task:")`. Inject relevant findings into the spawn prompt as a `## Context (from SSOT)` block.
2. **After a teammate result**, persist what should survive: `kdx_context_set("session:<sid>", "task:<id>:result", "<JSON>", "orch")` and key decisions.
3. **Teammates stay blind**: do not tell them the SSOT exists. Sole exception: a long-running orch-high worker producing many artifacts — give it one line: `Persist intermediate artifacts via kdx_context_set(scope="session:<sid>", key="<convention>", ...)`.

The SSOT survives spawns — use it for state the user can inspect later via `kdx_context_query`; skip it for ephemeral data the next teammate won't reuse.

## References

- **Prompt doctrine**: See [prompt-doctrine.md](references/prompt-doctrine.md) — WHAT vs HOW rules, before/after, 2026 sources. **Tool matrix**: [tool-matrix.md](references/tool-matrix.md)
- **Specialized agents**: See [specialized-agents.md](references/specialized-agents.md) — orch-janitor/changelog/critic contracts, frozen schemas, closing doctrine
- **Advanced patterns**: See [patterns.md](references/patterns.md) — fan-out, SendMessage re-entry, adversarial loop-until-dry
- **Agent teams**: See [agent-teams.md](references/agent-teams.md) — mandatory team lifecycle, teammate roles, task list, limits, hooks
- **Loops & continuous agents**: See [loops.md](references/loops.md) — three hard stops, loop tiers, Workflow tool, git-backed durable state
- **SSOT details**: See the `kdx-shared-agent-context-manager` skill
