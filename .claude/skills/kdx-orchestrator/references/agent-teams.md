# Agent Teams — real API, primary path

kdx-orchestrator runs as a **team lead** using `Agent()` spawns + the shared
task list + `SendMessage`. This file is the full mechanics; SKILL.md carries
only the must-knows.

## Why this path (not TeamCreate)

`TeamCreate`/`TeamDelete` **do not exist in this harness** — every invocation
that tried the "form the team via TeamCreate" sequence failed on step 1. Treat
the team-creation API as a one-time capability check: if `TeamCreate` exists,
prefer it; on this machine it currently does not, so the primary path is
`Agent()` spawns sharing a `team_name` string, coordinated via `TaskCreate`/
`TaskUpdate` and `SendMessage`. This still gives peer messaging and a shared
task list — the two things that matter — without a working `TeamCreate` call.

## Prerequisites (already satisfied on this machine)

- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `~/.claude/settings.json` (`env` block).
- Claude Code ≥ v2.1.32 (`claude --version`).

If `SendMessage`/`Task*` are altogether missing, fall back to plain `Agent()`
subagent dispatch (no `team_name`) and tell the user.

## Lifecycle (real tool API — verified)

1. **Check** — if `TeamCreate` exists as a callable tool, use it; otherwise skip straight to spawning (the common case here).
2. **Spawn teammates by role** — `Agent(subagent_type: "orch-<tier>", team_name:
   "<team>", name: "<unique>", prompt: ...)`. The `team_name` is what makes the
   agent a teammate rather than a one-shot subagent. The teammate honors that
   definition's `tools` allowlist and `model`; the body is appended to its system
   prompt (not replacing it). `SendMessage` + task tools are always available even
   if `tools` is narrow. A teammate does NOT inherit the lead's conversation
   history, and the `skills`/`mcpServers` frontmatter fields are ignored for
   teammates (they load skills/MCP from project+user settings). Put task facts,
   INCLUDING the `report_path` (see SKILL.md Report-File Contract), in the spawn prompt.
3. **Coordinate via the shared task list** — `TaskCreate(subject, description)`
   (tasks start `pending`, no owner), `TaskList`, `TaskGet`, `TaskUpdate(owner,
   status: pending|in_progress|completed|deleted, addBlocks, addBlockedBy)`. Assign
   with `owner: "<teammate name>"`; order with `addBlocks`/`addBlockedBy` (auto-unblock
   when prerequisites complete). File locking prevents claim races. There is no
   `depends_on`/`assigned_to`/`blocks` arg on `TaskCreate` — dependencies are set via
   `addBlocks`/`addBlockedBy` on TaskUpdate.
4. **Steer** — `SendMessage(to: "<name>", summary: "...", message: "...")`.
   Completion/idle notifications arrive automatically as new turns, but they are
   **content-less** — they do NOT carry the teammate's result. The lead must read
   the teammate's `report_path` file to get the actual report. Do not poll for
   notifications and do not nag an idle teammate (idle = waiting, normal) —
   see the Stall Ladder in SKILL.md if a report never materializes.
5. **Clean up** — shut each teammate down with `SendMessage(to, message: {type:
   "shutdown_request", reason: "..."})`. After that message, the teammate may
   still emit idle echoes — **ignore them, do not re-engage**. If `TeamDelete`
   exists, call it; otherwise there is nothing further to tear down.

State lives at `~/.claude/teams/{team}/config.json` and `~/.claude/tasks/{team}/`
when the team primitives are present, auto-generated and removed on cleanup/
session end. Never hand-edit or pre-author.

## Limitations (design around these)

- **No nested teams** — a teammate cannot spawn teammates. It MAY still use the
  `Agent` tool to spawn its own subagents (that is how orch-high nests).
- **`TeamCreate`/`TeamDelete` do not exist here** — do not depend on them; the
  `Agent()` + task-list + `SendMessage` path above IS the team.
- **`TaskOutput` does not retrieve teammate output** — it rejects teammate ids.
  Read the teammate's `report_path` file instead.
- **Completion/idle notifications carry no result** — they are a signal to go
  read the report file, not the report itself.
- **No in-process teammate resumption** after `/resume` or `/rewind` — the lead
  may message teammates that no longer exist; spawn fresh ones if so.
- **Task status can lag** — a teammate may forget to mark a task complete and
  block dependents. Nudge it (once) or update the status yourself.
- **Same-file edits clobber** — assign each teammate disjoint files.
- **Permissions set at spawn** — teammates inherit the lead's permission mode.

## Quality gates (optional hooks)

`TeammateIdle`, `TaskCreated`, `TaskCompleted` hooks can exit code 2 to send
feedback and keep a teammate working / block a bad task transition.

## Plan approval for risky teammates

For risky write work, spawn the teammate requiring plan approval: it stays in
read-only plan mode until the lead approves. Give the lead approval criteria in
the dispatch ("only approve plans with test coverage").

Docs: https://code.claude.com/docs/en/agent-teams
