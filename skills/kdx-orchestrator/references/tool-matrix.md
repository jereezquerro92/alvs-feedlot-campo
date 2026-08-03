# Tool Availability Matrix

## By Tier

| Tool | Orchestrator | Low | Medium | High |
|------|:-----------:|:---:|:------:|:----:|
| Read | yes | yes | yes | yes |
| Glob | yes | yes | yes | yes |
| Grep | yes | yes | yes | yes |
| Edit | no | no | yes | yes |
| Write | no | no | yes | yes |
| Bash | yes | no | yes | yes |
| Agent | yes | no | no | yes |
| WebFetch | yes | yes | yes | yes |
| WebSearch | yes | yes | yes | yes |
| TaskCreate/Update | yes | * | * | * |
| SendMessage | yes | * | * | * |

> **`*` = automatic for teammates.** This table's `tools` columns reflect each
> definition's `tools` allowlist. When an agent runs **as a teammate** (spawned
> with `team_name`), the harness grants `SendMessage` + all `Task*` tools
> regardless of the allowlist — never list them in a definition's `tools`. The
> "no" world only applies on the **subagent-fallback path** (no team), where a
> low/medium subagent reports solely to its caller and has no `SendMessage`.

`SendMessage` re-enters a named worker with context intact. Gated behind the agent-teams flag; falls back to a fresh `Agent()` dispatch when unavailable. orch-high additionally holds `Agent` to spawn its own subagents (not a nested team). The bound is the **dispatch budget** it carries, not a depth number — the harness caps overall tree depth; orch-high doesn't track its own.

`orch-critic` (sonnet, adversarial verifier) is a specialized read-only worker: Read/Glob/Grep/Bash(read-only)/WebFetch/WebSearch. See specialized-agents.md.

`orch-planner`/`orch-builder`/`orch-auditor` (all sonnet, the velocity loop) follow the same tool split as the generic tiers: planner and auditor are read-mostly (Read/Glob/Grep/Bash-read-only/WebFetch/WebSearch, no Edit/Write); builder is full write (adds Edit/Write). None can spawn sub-agents. See specialized-agents.md.

## By Scope

Tools are further restricted by scope, regardless of tier:

| Tool | scout | read | write |
|------|:-----:|:----:|:-----:|
| Read | yes | yes | yes |
| Glob | yes | yes | yes |
| Grep | yes | yes | yes |
| Edit | no | no | yes |
| Write | no | no | yes |
| Bash | no | read-only | yes |
| WebFetch | yes | yes | yes |
| WebSearch | yes | yes | yes |

**Effective access = tier AND scope.** A MEDIUM agent with `read` scope can use Bash but only for read commands (ls, cat, git log — not rm, mv, sed).

## Orchestrator Constraints

The orchestrator itself:
- **Does NOT** Edit or Write files directly — delegates to workers
- **Does** use Read, Glob, Grep, Bash for gathering context before dispatch
- **Does** use Agent to dispatch workers
- **Does** use TaskCreate/Update to track progress
- **Does** read reference files for preambles and patterns

## MCP Tools Available

No MCP servers are wired into the worker allowlists by default. If a server is
registered on this machine (per `~/.claude.json` / `mcp-servers.json`) and a task
needs it, add the specific `mcp__*` tools to that tier's definition and name the
server in the dispatch prompt — never inject a bare tool list the definition
already carries.

## Dispatch Shorthand

When constructing the prompt, state constraints concisely:

- **Low**: "TOOLS: Read, Glob, Grep, WebFetch, WebSearch. Nothing else."
- **Medium read**: "TOOLS: Read, Glob, Grep, Bash (read-only), WebFetch, WebSearch."
- **Medium write**: "TOOLS: Read, Glob, Grep, Edit, Write, Bash, WebFetch, WebSearch."
- **High**: "TOOLS: All tools including Agent."
