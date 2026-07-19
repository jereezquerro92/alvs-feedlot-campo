# Loops, Workflows & Continuous Agents (2026)

The team model (see [agent-teams.md](agent-teams.md)) is the default. Everything
in THIS file — loops, the Workflow tool, git-backed durable state — is **optional
layering** on top of it. Reach for it only when a single team pass can't express
the work.

## The three hard stops (contract, not advice)

Any loop the orchestrator runs — repeated waves, generation↔critique, a `/goal`
run, a cron tick — MUST encode all three, or it is forbidden:

1. **`MAX_ITER`** — a ceiling on iterations. No "until done" without a number.
2. **No-progress detection** — halt on N consecutive identical errors, or N
   consecutive empty diffs. A loop that isn't moving is burning money.
3. **Budget** — token/$ ceiling per loop AND per worker. Budget is a
   **required field** in any worker dispatch that runs inside a loop.

State these in the dispatch prompt as constraints. A worker with no declared
budget inside a loop should Quick Exit asking for one.

## Loop schema (6 blocks)

When framing a repeating job, fill these (community convention, not official):
`TRIGGER` (what starts a tick) · `SCOPE` (files/area) · `ACTION` (the named
skill/worker to run) · `BUDGET` (the three stops above) · `STOP` (completion
condition) · `REPORT` (what each tick writes back). A loop is a cron + a
per-tick decider, NOT a fixed-iteration job: each tick re-reads durable state
and decides afresh.

## Picking a loop tier

| Need | Use | Notes |
|---|---|---|
| Watch while you work, terminal open | `/loop` (session-scoped, polling, min 1 min, auto-expires 7 days; omit interval = self-pace 1min–1hr) | backed by CronCreate/CronList |
| Needs local uncommitted code, survives reboot | Desktop task | persistent local |
| Run with the laptop off | Cloud task / Routine (via `/schedule`, ScheduleWakeup, min 1 hr) | fresh clone each fire; research preview |
| Loop-until-done with a completion condition | `/goal` | works across turns; elapsed/turns/tokens overlay; pairs with orch-critic for loop-until-dry |
| Legacy escape hatch | system cron + `claude -p` | only when the above don't fit |

## Workflow tool (deterministic fan-out)

**Decision: hybrid.** Manual tiers + waves stay the DEFAULT. Use `Workflow`
only for large deterministic fan-out — audits, migrations, mass refactors over
dozens-to-hundreds of items where results should flow through script variables
**outside** the orchestrator's context.

- `agent()` / `parallel()` (barrier) / `pipeline()` (no barrier between stages) / `phase()`.
- Structured output via schema (validates + retries). Up to 16 concurrent
  (`min(16, cores-2)`), up to 1000 agents/run, ≤4096 items/call. Resumable
  (`resumeFromRunId` cache-hits the unchanged prefix). Saveable as a `/command`.
- Built-in `/deep-research`. `/effort ultracode` auto-plans workflows.

When NOT to use it: anything needing the orchestrator's judgment mid-stream, or
small N — the tier+wave model is lighter and keeps you in the loop.

## Agent Teams (the mandatory orchestration model)

**Decision: ALWAYS ON.** kdx-orchestrator forms an agent team on every
invocation — this is the default execution model, not an opt-in layer. Flag
`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set in `~/.claude/settings.json`.
Each teammate is a full Claude session coordinating via a shared task list
(`~/.claude/teams/{team}/`) and peer `SendMessage`. Full lifecycle, teammate
roles, limits, and hooks: [agent-teams.md](agent-teams.md).

Task primitives (real API): `TaskCreate(subject, description)`, `TaskList`,
`TaskGet`, `TaskUpdate(owner, status, addBlocks, addBlockedBy)`. Assign via `owner`,
order via `addBlocks`/`addBlockedBy` (auto-unblock), never a `depends_on`/`blocks` arg
on create. Plain `Agent()` subagents remain the fallback only when the team tools
are unavailable.

## Durable state (git-backed, complements the SSOT)

**Decision: documented, used for long/crash-prone runs only.** The `kdx_context_*`
SSOT (see SKILL.md) is the default working memory. For loops that must survive a
crash, a restart, or context compaction, ALSO externalize state to **git**, à la
the Anthropic long-running-harness and Gas Town:

- An Initializer step (runs once) writes a progress file + a feature/task list
  (all items start "failing") and makes an initial commit.
- Each loop tick reads that state, advances exactly one item, commits.
- Git history + progress file + feature list survive context loss — compaction
  alone does not. Never trust the model's context to carry plan state across a
  crash; assume any worker can die mid-task.

This guards the four classic failure modes: premature victory, undocumented
buggy progress, marking features done too early, and wasted re-setup. Use it
only for genuinely long runs; short interactive sessions stay on the SSOT alone.

## Secrets in loops

For loops that touch secrets, mirror the Managed-Agents vault model: real
credentials live only at the network boundary for allow-listed domains; the
model context sees a placeholder. Never let a loop persist a real secret into
git, the SSOT, or a worker prompt.
