---
name: kdx-wf-triage-and-fix
description: The triage-and-fix Workflow — takes one GitHub issue end to end (forest, tavern, camp, stalking, plaza: scout, triage, route, plan, build backend+frontend, secret-scan gate, blind review, publish) via a deterministic JavaScript Workflow script driving a cast of purpose-built agents with exact tool grants. Use when kodex says "triage-and-fix", "the party", "la taberna", "el campamento", "el cazador", names a node (hunter, falcon, hound, tavernkeeper, mage, warrior, archer, priest, owl, cat, mouse, shadow, bard), asks to run an issue through the workflow, or wants to edit the cast, the scenes, or the script.
---

# kdx-wf-triage-and-fix

One issue in; a pull request, a comment on that issue, or a new issue out. Everything
between is deterministic.

## Run it

```
Workflow({ name: 'triage-and-fix', args: { issue: '42', repo: 'kodexArg/some-repo' } })
```

`args.issue` may be a number, a URL, or free text — the hunter fetches it with `gh`.
`args.repo` is optional when the cwd is the repo.

**Prerequisites, both real:**

1. **Dynamic workflows must be enabled** for the session (`/config` → Dynamic workflows, or
   `/effort ultracode`). Without it the Workflow tool is not exposed and this skill cannot run.
2. **A fresh session** after the cast was installed — the agent registry loads at startup, so
   `wf-*` types do not resolve in a session that predates them.

To iterate on the script: edit it, then re-invoke. Prior `agent()` calls with unchanged
`(prompt, opts)` return cached results instantly — only what you edited re-runs:

```
Workflow({ scriptPath: '~/.claude/workflows/triage-and-fix.js', resumeFromRunId: 'wf_...' })
```

## The shape

```
forest     hunter ─┬─ falcon ──┐        mandatory fan-out: parallel() at script level
                   └─ hound ───┤        hound returns chunks, not paths (sonnet pin here)
                      the task ┘        pure script assembly, no agent call
                        ↓
tavern     tavernkeeper                 an IF on hunter.domain — not an agent
                        ↓
           mage ─── owl / cat / hound / mouse   optional fan-out: mage's own Agent tool,
                        ↓                       one background message, 10-min watchdog
                     the plan                   (mage cannot write; splits backend/frontend)
                        ↓
camp       warrior (backend) ║ archer (frontend)  parallel builders, each own worktree —
                        ↓                         a builder spawns only if its slice is non-empty
                     priest                        gate: clean|blocked on the combined diff
                        ↓            (blocked kills the run here — nothing below it runs)
stalking   shadow (zero tools, sees only the combined diff)
                        ↓
plaza      bard → PR (merges 2nd builder branch into 1st) · comment on the issue · new issue
```

Up to nine `agent()` calls, depending on whether one or both builders spawn. Quick exits:
falcon `emergencia` (duplicate), hunter `outOfScope: recurring-defect` (the vampiro — a
defect that will not stay dead), the priest's `blocked` (a secret in the diff), or unfit
ground.

## The two things to understand before editing

**Reliability has exactly three sources here** — model tier, tool grant, and the schema that
closes the output. It is never a property of a name. The owl is not reliable because it is an
owl; it is reliable because a closed question against an allowlisted first-party domain is a
reliable *shape*. An earlier draft of this system wrote "the owl is the only trustworthy
familiar" and a model read that as an engineering fact. Do not reintroduce that.

**The fiction is a render, never an input.** Prey names, icons and the party's spoken lines
are printed so a human can read a run. They are a closed set, written in advance, and no node
produces or reads one. Strip every animal from this skill and every outcome is byte-identical.

## Files

Everything is a real file in this repo — no symlink, no copy of anything, and no
dependence on a machine-global harness ([[adr-14-harness]]). Each piece lives in the one
home its consumer reads it from, which is why they are not all under this skill:

| File | What it is |
|---|---|
| `.claude/workflows/triage-and-fix.js` | **The script.** Lives here because that is where the runtime discovers named workflows — not under this skill. One real copy; there is no second one to drift from. |
| `agents/wf-*.md` | **The ten cast definitions** (the hero is one character and two agents), in the repo's agent SSOT, reached as `.claude/agents/`. **The `tools:` list is the enforcement**, not the prompt. Two members of the party are not agents at all: the task and the tavernkeeper are script. |
| `team-party.md` | The shared context prepended to every node's prompt, so each knows its place. **Inlined into the script** as `TEAM_PARTY` — the script has no filesystem. Edit both together. |
| `workflows/validate.mjs` | Applies the runtime's own gate to the script. Run it after every edit: `node workflows/validate.mjs ../../workflows/triage-and-fix.js` (needs `bun add acorn acorn-walk` once). |
| `references/cast.md` | The node spec: verified runtime contract, the prey table, what each node owns, what is still open. Read before changing any node. |
| `references/scenes.md` | The scene bank: 13 closed ASCII frames with slots. A richer render than the script's current `log()` line; nothing in it is generated at runtime. |

## Editing rules

- **Never author a `quote`/`reason` field into a schema.** The lines live in the script's
  `SAY` table; a generated line is model output reaching the log, which is a channel.
- **Before adding a node, ask what it decides that an upstream node was not already holding
  the context to decide.** If the answer is "the same thing, with less to go on", it is not a
  gate — it is a worse copy, and it belongs in the script as an `if`. That is how the
  tavernkeeper stopped being an agent.
- **A grant is a claim; a prompt is a wish.** If a node must not do something, take the tool
  away in its definition — do not ask it nicely in prose.
- **Every `agent()` call needs a `schema`** and every call site must handle `null` (the
  subagent can die).
- **`parallel()` takes thunks**: `() => agent(...)`, never a promise.
- **No `Date.now()` / `Math.random()` / `new Date()`** — they throw and break resume.
- Changing the specialist roster is one edit to `DOMAIN`/`DOMAINS` in the script.

Full runtime contract and the resolved/open design questions: `references/cast.md`.
