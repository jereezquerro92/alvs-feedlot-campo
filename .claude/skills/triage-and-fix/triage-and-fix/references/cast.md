# cast.md — the kwf-* node spec

SSOT for what every node in **triage-and-fix** *is*, mechanically. The playbook
is `SKILL.md`; REQUIREMENTs are `references/deps.md`; host spawn/model pins are
`references/runtimes.md`.

## Runtime contract (shared)

- The **main agent is the script.** `SKILL.md` is the procedure; execute it phase
  by phase. Native `Workflow` (Claude) is optional sugar, not required.
- Cast SSOT: `docs/agents/kwf-*.md`. Frontmatter declares `name`, `description`,
  `tools` (allowlist; empty = zero tools), optional `subagents`. Always declare
  `tools`.
- Output contract = final message as a **YAML block**. Hosts without schema
  enforcement still parse YAML and branch on typed fields.
- Dead / broken contract → phase abort (`hunter-failed`, `plan-failed`,
  `build-failed`, `gate-failed`, `review-failed`, `doctrine-failed`,
  `publish-failed`).
- **Resume** the same planner instance for the doctrine loop when the host
  supports it (cap 2). Otherwise re-dispatch with full prior plan + findings.
- **Tier pins and spawn mechanics are host-specific** — see `runtimes.md`.
  Tier *intent* (cheap/mid/high/heavy) is what this table means; model strings
  are not portable.
- Builders create their own git worktree as first act (no host isolation API
  required).

## The standing rules (unchanged from the Claude original)

1. **The fiction is a render, never an input.** Prey names and the Spanish lines at the top
   of each definition are a closed set, written in advance, printed for humans. No node
   produces or reads one. Strip them and every outcome is identical.
2. **A grant is a claim; a prompt is a wish.** Every "cannot" below is a `tools:` entry
   that is absent, not a sentence that asks nicely.
3. **A node that re-derives, at lower context, a judgment an upstream node already holds
   is not a gate — it is a worse copy.** That is why routing is an `if` on `hunter.domain`.

## Cast

| # | Node | Phase | agentType | tools (exact) | tier intent |
|---|---|---|---|---|---|
| 1 | 🎯 hunter | forest | `kwf-hunter` | Bash, Read, Glob, Grep | low |
| 2 | 🦅 falcon | forest | `kwf-falcon` | Bash | low, cheap |
| 3 | 🐕 hound | forest | `kwf-hound` | Read, Glob, Grep | low |
| — | 📋 the task | forest→tavern | *the main agent assembles a string* | — | — |
| — | 🍺 routing | tavern | *an `if` on `hunter.domain`* | — | — |
| 4 | 🧙 mage | tavern | `kwf-mage` | Read, Glob, Grep, Agent, Bash* | **k3-256k** |
| 4s | 🪄 sorcerer | tavern | `kwf-sorcerer` | Read, Glob, Grep, Agent, Bash* | **K2.7 highspeed** (mid) |
| 4a | 🦉 owl | tavern | `kwf-owl` | WebSearch, FetchURL | K2.7 (cheapest) |
| 4b | 🐈‍⬛ cat | tavern | `kwf-cat` | WebSearch, FetchURL | K2.7 (cheapest) |
| 4c | 🐕 hound | tavern | `kwf-hound` | Read, Glob, Grep | K2.7 (cheapest) |
| 4d | 🐁 mouse | tavern | `kwf-mouse` | Read, Glob, Grep | K2.7 (cheapest) |
| 4e | ⚖️ inquisitor | tavern | `kwf-inquisitor` | Read, Glob, Grep | **k3-256k** |
| 5a | ⚔️ warrior | camp | `kwf-warrior` | Read, Glob, Grep, Edit, Write, Bash | high (inherits caller) |
| 5b | 🗡️ thief | camp | `kwf-thief` | Read, Glob, Grep, Edit, Write, Bash | high (inherits caller) |
| 5c | 🪓 dwarf | camp | `kwf-dwarf` | Read, Glob, Grep, Edit, Write, Bash | high (inherits caller) |
| 5d | 🏹 archer | camp | `kwf-archer` | Read, Glob, Grep, Edit, Write, Bash | high (inherits caller) |
| 5e | 🧝 elf-mage | camp | `kwf-elf-mage` | Read, Glob, Grep, Edit, Write, Bash | **k3-256k** |
| 5f | 🛡️ paladin | camp | `kwf-paladin` | Read, Glob, Grep, Edit, Write, Bash | **k3-256k** |
| 6 | 🙏 priest | camp | `kwf-priest` | **none** | cheap |
| 7 | 👤 shadow | stalking | `kwf-shadow` | **none** | low |
| 8 | 🎻 bard | plaza | `kwf-bard` | Bash | high |

\* The mage's `Bash` is granted for the familiar watchdog loop only; any other use is a
defect. Its `subagents:` allowlist (`kwf-owl`, `kwf-cat`, `kwf-hound`, `kwf-mouse`) is the
enforcement that it can spawn *only* its familiars.

## What changed vs the Claude cast

- **The camp is a specialist roster, N instances.** The plan emits
  `slices: [{name, builder, files}]` — path-disjoint file sets, each assigned to a
  specialist: ⚔️ `warrior` (backend), 🗡️ `thief` (frontend), 🪓 `dwarf` (devops/infra),
  🏹 `archer` (design/cosmetic), plus the k3-256k heavy pair 🧝 `elf-mage` (very
  complex) and 🛡️ `paladin` (heavy devops). One parallel dispatch — an `Agent` call per
  slice in a single message, each `subagent_type` the slice's own specialist. Same
  guarantees as the old single builder: own worktree, own branch, real diff,
  path-disjoint so the bard can merge cleanly. The Claude cast's warrior+archer are
  back, as a roster instead of a hardcoded pair.
- **The sorcerer plans trivial game.** The hunter's `difficulty` enum gained `trivial`;
  a trivial tag routes the tavern to 🪄 `kwf-sorcerer` on the mid tier
  (`kimi-code/kimi-for-coding-highspeed` — the mid rung of the Kimi ladder: K2.7
  standard < K2.7 highspeed < k3-256k < k3 1M; there is no Sonnet-shaped model, the
  highspeed K2.7 is the mid). Same doctrine-first read, same familiars, same contract —
  a trivial plan does not earn k3's fee.
- **The plan carries `baseRef` and `prRequirements`** — see `deps.md`. When the work
  trusts an unmerged PR, `baseRef` is that PR's head branch and the bard declares the
  `requires:N` labels at publish time.
- **The bard owns the cascade.** Any action that defers work (label or close-unmerged) is
  followed by `kwf-deps cascade <pr>`. Skipping it leaves dependent PRs looking alive when
  their ground is gone.
- **Schemas → YAML final-message contracts.** Same fields, same closed enums, different
  envelope. The contract is stated in each definition's *Output contract* section and is
  the only thing that travels between nodes.

## What each node owns (one decision each)

- **hunter** — whether the ground is fit (toolchain, gh, constitution, **PR
  requirements**), the two tags, the domain, the vampiro call.
- **falcon** — the duplication abort (`emergencia`). Severity is about duplication, never
  danger.
- **hound** — which code references are worth surfacing. No gate; confidence ceiling
  `medium` by definition. Returns chunks, never bare paths.
- **mage** — what the change should be, split into N slices, each assigned its camp
  specialist; the baseRef the builders branch from; the PRs the result will require.
  Cannot begin making it. **Reads the law
  before planning**: the PRD itself, in full, always; the binding ADRs itself, after the
  mouse's mandatory relevance triage. Declares what it read in `doctrine`.
- **sorcerer** — everything the mage owns, for `difficulty: trivial` game only, on the
  mid tier. Same doctrine-first read, same contract, same familiars.
- **inquisitor** — whether the *plan* complies with the PRD, active ADRs, and
  assertion/TDD completeness when assertions are touched, before any builder wakes.
  Judges plans, never code; cites rule + plan step on every finding; never re-plans.
  Its `violation` loops the plan back to the **resumed** planner (context intact),
  capped at 2; a third violation is the `doctrine-failed` abort.
- **the camp specialists** (warrior, thief, dwarf, archer, elf-mage, paladin) — whether
  their slice of the plan survives contact with the files. A step that
  cannot be executed as written is a `deviations` finding, never a silent improvement.
- **priest** — whether anything in the combined diff must never ship. It sees what the
  camp **did**, never the mage's plan: deeds, not intent. `blocked` is
  terminal; findings never quote the value.
- **shadow** — whether the code stands up with nothing else in hand. Blindness is the
  instrument.
- **bard** — hunted or not, and the one published artifact. Plus the defer cascade.

## Still open

- **Retry loop from shadow `needs-work` back to builders** — still unbuilt; the doctrine
  loop (inquisitor → resumed mage, cap 2) is now the proven template if this is wanted.
- **Priest appeal path** — none; a false positive means re-planning around the pattern.
- **Tier enforcement** — pins live at dispatch (explicit `model` per call, per the docs);
  the `model_preference: secondary` + `[secondary_model]` in config is the fallback for
  the mage and the k3 camp pair (elf-mage, paladin), active machine-wide
  (`KIMI_CODE_EXPERIMENTAL_SECONDARY_MODEL=1` in `~/.bashrc`, applies
  to new sessions). The sorcerer and the familiars have no frontmatter lever at all —
  their tiers exist only as dispatch-time pins (by the orchestrator, and by the
  mage/sorcerer for familiars).
- **Post-bard hooks** — **in force**: after bard, the orchestrator runs
  `docs/hooks/guardian-dispatch` and `assertion-review` when assertions moved. See
  Post-bard in `SKILL.md` and [[adr-04-issue-delivery]]. Verifier / smoke-test pause
  remain open.
- **Cursor/Grok registry** — no native `kwf-*` types; prompt-inject via `Task` per
  `runtimes.md`. First-class registry support would remove that adapter layer.
