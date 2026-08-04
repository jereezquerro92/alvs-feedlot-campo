---
name: triage-and-fix
description: >
  Issue→PR delivery party — forest, tavern, camp, stalking, plaza: scout, plan,
  N parallel camp specialists, secret-scan gate, blind review, publish. Driven by
  the kwf-* cast under docs/agents/. PR REQUIREMENT system (requires:N, defer
  cascade via kwf-deps). Post-plaza: guardian-dispatch + assertion-review.
  Assertions are the entry path for important features (TDD first). Use when
  kodex says "triage-and-fix", "the party", names a kwf-* node, runs an issue
  through delivery, or defers/requires PRs with kwf-deps.
license: MIT
compatibility: >
  Requires gh authenticated, git with worktree support, python3. Cast lives in
  docs/agents/kwf-*.md. Dispatch mechanics differ by host — see
  references/runtimes.md (Kimi, Claude Code, Cursor/Grok). A session started
  before agents were installed will not resolve kwf-* types on hosts that
  registry-load at startup.
metadata:
  author: kodexArg
  version: "1.0.0"
---

# triage-and-fix

One issue in; a pull request, a comment on that issue, or a new issue out.

Ships **inside harness-default** (`docs/agents/kwf-*` + this skill). Binding ADR:
`docs/adrs/adr-04-issue-delivery.md` (law: `adr-01`, tooling: `adr-02`).
Runtime spawn/model map:
`references/runtimes.md`.

Upgrades over the early Claude `kdx-wf-triage-and-fix` cast:

1. **Specialist camp**: mage splits into N path-disjoint slices; each gets a
   builder — ⚔️ warrior, 🗡️ thief, 🪓 dwarf, 🏹 archer, plus heavy 🧝 elf-mage /
   🛡️ paladin — each in its own git worktree.
2. **Trivial → sorcerer**: `difficulty: trivial` plans on the mid tier.
3. **PR REQUIREMENT system**: `requires:N` labels; `bin/kwf-deps cascade` on defer.
4. **Issue disposition labels**: stop-exits apply `needs-info` | `blocked` |
   `deferred` | `unresolvable` | `duplicate` so hunts do not loop
   (`references/disposition.md`, [[GH]], adr-04).
5. **Assertions + guardians**: doctrine-first plan, inquisitor TDD gate on
   assertion-touching plans, post-bard `guardian-dispatch` + `assertion-review`.

## How it runs

**You — the main agent — are the script.** Follow this playbook exactly: same
phases, order, quick exits, YAML contracts. Determinism lives in closed output
contracts and your branching on typed fields — never in prose.

How you *spawn* a node depends on the host (native `kwf-*` vs prompt-injected
`Task`). Read `references/runtimes.md` once, then dispatch. Forest trio and camp
specialists fan out in parallel in one message when the host allows. A node that
dies or returns garbage is `null` → that phase's abort below.

## The shape

```
forest     hunter ─┬─ falcon ──┐        parallel: 3 nodes
                   └─ hound ───┤
                      the task ┘        you assemble it — a string, not an agent
                        ↓
tavern     routing (IF on hunter.domain + hunter.difficulty) — not an agent
                        ↓
           mage (heavy) | sorcerer (mid, trivial only)
                ─── owl / cat / hound / mouse   familiars
           (PRD + binding ADRs FIRST — doctrine before plan)
                        ↓
                     the plan  (N path-disjoint slices + builder + baseRef)
                        ↓
           ⚖️ inquisitor ── plan vs PRD/ADRs/assertions-TDD ──┐
              ↑                │                              │
              └── violation: RESUME same planner ─────────────┘  (≤2 loops)
                        ↓
camp       specialist × N ══ parallel, each own worktree+branch
           ⚔️ warrior · 🗡️ thief · 🪓 dwarf · 🏹 archer
           🧝 elf-mage · 🛡️ paladin — heavy pair
                        ↓
                     priest (gate: clean|blocked on combined diff)
stalking   shadow (zero tools, combined diff only)
plaza      bard → ONE PR | comment | new issue
                        ↓
           post-bard (you) — guardian-dispatch + assertion-review
                        ↓
           kwf-deps cascade — whenever anything is deferred
```

## The run, step by step

### Forest — three parallel nodes in one message

- **kwf-hunter**: hunt issue `<ref>` in `<owner/repo>` (or cwd). Fetch with gh,
  four ground checks, domain from `<domain roster>`, tags. Output contract.
- **kwf-falcon**: GitHub-only duplicate/regression scout. Output contract.
- **kwf-hound**: which code does this touch? Return lines in `chunk`.

Quick exits, in order (every stop **labels** per `references/disposition.md`):

1. Hunter died → abort `hunter-failed`.
2. `dispositionStop` ≠ `none` → **already-dispositioned**: one-line note; do not
   re-plan. Label stays until a human removes it.
3. `infoComplete` false → **needs-info**: comment the questions; label
   `needs-info`.
4. `outOfScope: recurring-defect` → **vampiro** 🧛: comment; label `deferred`.
5. Falcon `emergencia` → **duplicate** 🦅: comment canonical ref; label
   `duplicate`.
6. `constitutionOk` false → **ground-unfit** (law): comment file+rule; label
   `unresolvable`.
7. `stackDepsOk` or `ghConnected` false → **ground-unfit** (env): comment;
   label `blocked`.
8. `requirementsOk` false → **requirement-unmet**: comment naming unmet
   `Requires PR: #N`; label `blocked` — do **not** use `deferred` (the
   requirement may still land).

Complexity that cannot finish in one hunt (planner refuses / must split beyond
this run) → comment the split; label `deferred`.

**The task** = issue title+body verbatim + hunter tags/notes + falcon + hound.
String assembly only — no agent.

### Tavern — mage, or sorcerer for trivial

Routing is an `if` on `hunter.difficulty` — no router node.

- `trivial` → **kwf-sorcerer** (mid tier — see runtimes.md).
- `easy` | `medium` | `hard` → **kwf-mage** (heavy tier).

**Full-fidelity handoff, always** — never summarize the task for the planner.
Familiars ride the cheap tier. Dispatch with task, domain brief, **PRD path**,
**ADR directory**, and posture (`hard`/`large` → familiars before commit).

Planner died → `plan-failed`.

### Doctrine loop — before camp

Dispatch **kwf-inquisitor** (heavy) with the complete plan + doctrine pointers.
It judges PRD, ADRs, and assertion/TDD completeness on assertion-touching plans.

- `compliant` → camp.
- `violation` → **resume same planner** with findings; re-review. Cap **2** loops;
  third violation → abort `doctrine-failed`.
- Inquisitor died → `review-failed`.

### Camp — N parallel specialists, then priest

- Empty plan → `empty-plan`.
- One parallel dispatch: `kwf-<slice.builder>` per slice (own worktree, own
  branch, own files only). Heavy pair: elf-mage, paladin on heavy tier.
- **Assertion / TDD rule.** If `files` include `docs/assertions/**` or steps
  claim a law: read `docs/TDD.md` + the assertion → write/link proving tests
  under `### Tests` → implement until green. Never invent assertions; never
  stamp `verified` (assertion-review owns that). TDD departures → `deviations`.
- Builder returned nothing → `build-failed`.
- Combined diff → **kwf-priest**. `blocked` ends the run (nothing published).
  Priest died → `gate-failed`.

### Stalking

**kwf-shadow** sees the combined diff only. Died → `review-failed`.

### Plaza

**kwf-bard**: issue, plan, builder YAMLs, combined diff, shadow + priest verdicts.

- 0 committed → comment only.
- 1 branch → push, one PR.
- N branches → merge into first (path-disjoint), one PR.

`kwf-deps requires` / `cascade` as needed. Bard died → `publish-failed`.

### Post-bard — close the batch (binding in this harness)

1. **Guardian dispatch.** From repo root:
   `python3 docs/hooks/guardian-dispatch --bundle <baseRef>` (adr-03 rule 10).
   Paste the bundle payload into each owed guardian's prompt; dispatch all
   owed guardians in one turn. Honor `violation` / `danger` / `needs-new-adr`.
2. **Assertion review.** If the combined diff touches `docs/assertions/**`
   (except `assertion-00-discipline.md`), run
   `docs/skills/assertion-review/SKILL.md`. Unmet → batch not closed; TDD
   first. Ill-formed → stop for the owner.

Cast and skill already live in this tree — do not maintain a second SSOT.

## Issue disposition (stop-the-loop)

| Label | Meaning |
|---|---|
| `needs-info` | Ask for requirements / clarification; wait for human. |
| `blocked` | Waiting on decision, unmet PR requirement, or env. |
| `deferred` | Hunt called off — complexity, cascade, or vampiro. |
| `unresolvable` | **Not resolvable** — constitution / permanent no. |
| `duplicate` | Confirmed duplicate; work the canonical issue. |

Re-hunt is forbidden while any of these remain. Spec:
`references/disposition.md`. Names live in [[GH]].

## The REQUIREMENT system (PR labels only)

| Label | Meaning |
|---|---|
| `requires:<N>` | Do not merge before PR #N. |
| `deferred` | Hunt called off — directly or by cascade (PRs). |

On **issues**, unmet PR requirements use `blocked`, not `deferred`.
On **PRs**, deferred = label present **or** closed unmerged. Spec:
`references/deps.md`.

```
docs/skills/triage-and-fix/bin/kwf-deps requires <pr> <N...> [--repo R] [--dry-run]
docs/skills/triage-and-fix/bin/kwf-deps check <pr> [--repo R]
docs/skills/triage-and-fix/bin/kwf-deps cascade <pr> [--repo R] [--dry-run] [--force]
docs/skills/triage-and-fix/bin/kwf-deps lift <pr> [--repo R] [--dry-run]
docs/skills/triage-and-fix/bin/kwf-deps status <pr> [--repo R]
```

Optional Actions trigger: `extras/gha-kwf-deps.yml`.

## Editing rules

- Reliability = model tier + tool grant + closed output contract — never a name.
- A grant is a claim; a prompt is a wish — enforce via `tools:` in `docs/agents/kwf-*.md`.
- Fiction is a render, never an input.
- Before adding a node: what does it decide that an upstream node already held?
- Only YAML contracts travel between nodes.

## Files

| File | What it is |
|---|---|
| `docs/agents/kwf-*.md` | 18 cast definitions — `tools:` is enforcement |
| `bin/kwf-deps` | REQUIREMENT / defer-cascade CLI |
| `references/cast.md` | Node spec: contracts, tiers, ownership |
| `references/deps.md` | REQUIREMENT system spec (PRs) |
| `references/disposition.md` | Issue stop labels / anti-loop |
| `references/runtimes.md` | Kimi / Claude / Cursor-Grok dispatch map |
| `extras/gha-kwf-deps.yml` | Optional Actions cascade trigger |
| `tests/test-deps.py` | Local kwf-deps harness — `python3 tests/test-deps.py` |
