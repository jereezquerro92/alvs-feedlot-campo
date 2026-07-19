# Advanced Orchestration Patterns

## Fan-Out

Dispatch N independent workers in a single message. Each carries a `report_path`
(see SKILL.md Report-File Contract). Collect results by **reading each report
file** — completion notifications are content-less signals only.

```
# Single message with multiple Agent calls:
Agent(subagent_type: "orch-medium", name: "writer-auth", run_in_background: true, isolation: "worktree",
  prompt: "Scope: write\n\n## Task\nRefactor auth module\n\nreport_path: <scratchpad>/writer-auth-report.md\n\nAgent name: writer-auth")

Agent(subagent_type: "orch-medium", name: "writer-tests", run_in_background: true, isolation: "worktree",
  prompt: "Scope: write\n\n## Task\nAdd tests for user service\n\nreport_path: <scratchpad>/writer-tests-report.md\n\nAgent name: writer-tests")

Agent(subagent_type: "orch-low", name: "reader-deprecated", run_in_background: true,
  prompt: "Scope: read\n\n## Task\nFind all usages of deprecated API\n\nreport_path: <scratchpad>/reader-deprecated-report.md\n\nAgent name: reader-deprecated")
```

**Rules:**
- Max 6 agents per wave (manual waves). For deterministic fan-out over **dozens to hundreds** of items, prefer the `Workflow` tool instead (see loops.md) — `parallel()`/`pipeline()` run up to 16 concurrent / 1000 agents in background with results flowing through script variables, not your context.
- Wait for ALL agents in a wave before starting the next — read each `report_path`, not the chat turn
- For write-scope agents: merge worktree branches via `git merge {branch}` after wave completes; verify via the Write-Scope Verification rule before trusting the merge
- Worktrees with no changes are auto-cleaned by the harness
- Trace deep trees by `agent_id`/`parent_agent_id`; a branch stuck on a permission prompt shows up in `claude agents --json` as `waitingFor` — that's the Stall Ladder trigger (SKILL.md): one nudge, then read the report file directly, then verify the artifact yourself.

**Wave hard stops (mandatory — same three as any loop):** a multi-wave run must declare a `MAX_ITER` ceiling on waves, halt on no-progress (a wave where every worker returns empty diffs or repeats a prior failure), and carry a token/$ budget. Encode these whenever waves repeat; a one-shot fan-out only needs the budget.

## Sequential Pipeline

Output of worker A feeds into worker B. Do NOT parallelize — B depends on A.

```
1. Dispatch scout -> get complexity assessment (report_path given at dispatch)
2. Read scout's report file frontmatter -> decide tier
3. Dispatch worker at decided tier with scout's context in prompt + its own report_path
4. Read worker's report file -> if needs follow-up, dispatch next worker
```

The orchestrator passes relevant parts of A's result into B's prompt.

## Scout-Then-Dispatch

The canonical pattern for uncertain tasks:

```
1. Agent(subagent_type: "orch-low", name: "scout-task1", run_in_background: true,
     prompt: "Scope: scout\n\n## Task\nAssess complexity of: {task}\n\nreport_path: <scratchpad>/scout-task1-report.md\n\nAgent name: scout-task1")

2. Read scout report file frontmatter:
   - complexity -> understand the task
   - recommended_effort -> map to orch-low, orch-medium, or orch-high
   - worktree_needed -> whether to add isolation: "worktree"

3. Read scout report body for context (file paths, risks)

4. Dispatch real worker with:
   - subagent_type = orch-{recommended_effort}
   - Scope = based on task type
   - Scout's findings embedded in prompt as context
```

Skip scouts when: files and scope are already known, complexity is obvious.

## Retry with Enrichment

When a worker's report file shows `status: false`:

```
1. Read `resolution` field (from the report file, not chat)
2. If "QUICK EXIT: {reason}":
   - Extract what's missing
   - Gather it yourself (Read, Grep, etc.)
   - Re-dispatch with enriched prompt
3. If other failure:
   - Read body for details
   - Fix the prompt and retry, or escalate one tier
4. Max 2 retries per task
```

**Enrichment example:**
```
# Original: "QUICK EXIT: Can't find the database schema"
# Orchestrator gathers schema, then:

Agent(subagent_type: "orch-medium", name: "writer-migration-r1", isolation: "worktree",
  run_in_background: true,
  prompt: "Scope: write\n\n## Task\nAdd migration for user roles\n\nContext (from orchestrator):
Schema is in db/schema.sql. Key tables:
- users (id, email, role_id)
- roles (id, name, permissions)\n\nAgent name: writer-migration-r1")
```

## Escalation Ladder

```
orch-low (failed) -> orch-medium (retry with more context)
orch-medium (failed) -> orch-high (retry with justification)
orch-high (failed) -> report to user (exhausted options)
```

Each escalation includes ALL context from previous attempts so the higher-tier agent doesn't repeat failed paths.

## Agent Re-Entry: SendMessage vs fresh dispatch

There are **two** ways to continue work. `name:` is a re-entry handle, not just a log label.

**A. Continue with context intact — `SendMessage`** (preferred when the prior worker's reasoning is worth keeping):

```
SendMessage(to: "writer-migration", summary: "schema facts to continue migration", message: "Schema is in db/schema.sql. Tables: users(id, email, role_id), roles(id, name, permissions). Continue.")
```

The addressed worker resumes in background with its full context — no re-explaining what it already did. One message per recipient (no multi-recipient syntax). Idle workers emit content-less notifications when they go quiet — that's a signal to check its `report_path`, not the result itself. (Gated behind the agent-teams flag; if `SendMessage` is unavailable, fall back to B.)

**B. Fresh `Agent()` dispatch** (preferred when you want clean context — the prior attempt went down a bad path and you don't want it anchored):

```
Agent(subagent_type: "orch-medium", name: "writer-migration-r2", isolation: "worktree",
  run_in_background: true,
  prompt: "Scope: write\n\n## Task\nAdd migration for user roles\n\nContext (from orchestrator):\nSchema is in db/schema.sql. Tables: users(id, email, role_id), roles(id, name, permissions)\n\nAgent name: writer-migration-r2")
```

**Choosing:** Quick Exit for missing context → `SendMessage` (cheapest, keeps progress). Worker looped on a wrong approach → fresh dispatch (clean slate). Either way, max 2 continuations per task before reporting failure.

## Adversarial Verification (loop-until-dry)

Generation↔critique. A producing worker claims done; `orch-critic` (sonnet) tries to REFUTE it within a budget. Convergence = no witness of failure found.

```
1. Producer (orch-medium/high, write) -> claims status:true + acceptance criteria met
2. orch-critic (read-only) <- the claim + its acceptance criteria + a budget
3. Critic returns:
   - witness_found:true  -> SendMessage the producer the witness; it fixes; back to step 2
   - witness_found:false -> critique-resilient; accept and move on
4. HARD STOPS bound the loop (never unbounded retry):
   - MAX_ITER reached (ceiling on producer<->critic rounds)
   - no-progress: critic returns the same witness twice, or producer diff is empty
   - budget (tokens/$) for the loop exhausted
```

Use for anything where "looks done" is not enough: security-sensitive changes, migrations, public-facing behavior. Skip for trivial/throwaway work.

## Parallel Read + Serial Write

Common refactoring pattern:

```
Wave 1 (parallel reads — all orch-low):
  reader-imports: "Find all files importing module X"
  reader-tests: "Find all tests for module X"  
  reader-api: "Read module X and list its public API"

Wave 2 (single write — orch-medium, informed by all reads):
  writer-refactor: "Refactor module X. Imports: {reader-imports}. Tests: {reader-tests}. API: {reader-api}."
```

The write wave has full context from reads, reducing Quick Exits.

## Batch Assessment

For large task lists, scout everything first:

```
Wave 1: N orch-low scouts in parallel, one per item
Wave 2: Group by recommended_effort
Wave 3: Dispatch grouped workers (all lows together, all mediums together)
```

Prevents over-allocating high-effort agents to simple tasks.
