# Runtime adapters — triage-and-fix

The playbook (`SKILL.md`) and every `kwf-*` YAML contract are identical across
hosts. Only **how you spawn a node** and **which model tier string you pass**
change. Read this file before the first dispatch on a host.

| Tier intent | Meaning |
|---|---|
| cheap / low | Scout, familiar, priest, shadow |
| mid | Sorcerer (trivial plans only) |
| high | Camp builders (warrior/thief/dwarf/archer), bard |
| heavy | Mage, inquisitor, elf-mage, paladin |

## Kimi Code CLI

**Native.** Cast files in `docs/agents/kwf-*.md` resolve when that directory is
on `extra_agent_dirs` in `~/.kimi-code/config.toml` (project clone path, not a
sibling repo). Skill on the Kimi skill path (symlink
`docs/skills/triage-and-fix` → `~/.kimi-code/skills/triage-and-fix`).

Dispatch: `Agent` with `subagent_type: kwf-<name>`, parallel forest/camp in one
message. Pin models at the call:

| Tier | Model pin |
|---|---|
| cheap / low | `kimi-code/kimi-for-coding` |
| mid | `kimi-code/kimi-for-coding-highspeed` |
| heavy | `kimi-code/k3-256k` |
| high | inherit caller (or highspeed when upgrading) |

Fallback: mage / elf-mage / paladin may declare `model_preference: secondary`
bound to `kimi-code/k3-256k` when the `Agent` tool omits `model`.
Tools: `FetchURL` (not `WebFetch`), `WebSearch`.

## Claude Code

**Native via symlink.** Template ships `.claude/agents` → `docs/agents`. Fresh
session after install so `kwf-*` types load. Wire the skill into Claude skill
discovery (symlink or project skills path).

Dispatch: `Agent` with `subagent_type: kwf-<name>` — same playbook as Kimi
(**main agent is the script**). Optional: a deterministic `Workflow` script may
wrap the same phases later; not required.

| Tier | Model pin |
|---|---|
| cheap / low | Haiku-class |
| mid | Sonnet-class |
| high / heavy | Sonnet or Opus for mage/inquisitor/heavy builders |

Tools: `WebFetch` where Kimi agents say `FetchURL` — grant the host's equivalent
in the agent frontmatter if the runtime rejects unknown tool names.

## Cursor / Grok

**No native `kwf-*` registry.** Cursor `Task` subagent types are a fixed enum.
The main agent still **is the script**: for each node, `Read`
`docs/agents/kwf-<name>.md`, then `Task` with a mapped worker and a prompt that
**inlines that file** plus the phase handoff, requiring the YAML output
contract as the final message.

| Tier intent | Cursor `subagent_type` |
|---|---|
| cheap / low | `orch-low` (read-only scouts/familiars/priest/shadow) |
| mid | `orch-medium` |
| high | `orch-medium` or `generalPurpose` (builders that write) |
| heavy | `orch-high` or `generalPurpose` (mage, inquisitor, elf-mage, paladin) |

Builders that must edit: use a write-capable worker (`orch-medium` /
`generalPurpose`), never `orch-low`. Priest and shadow stay tool-free in
prompt even if the worker could use tools — instruct "tools: none; judge only."

Parallelism: fan out forest (hunter+falcon+hound) and camp slices as parallel
`Task` calls in one turn. Doctrine loop: `resume` the same planner Task when
the host supports it; otherwise re-dispatch with the full prior plan +
inquisitor findings (worse, but legal).

Grok on this host follows the same Cursor adapter. Prefer heavy tiers for mage
and inquisitor when available.

## Souls

Every `kwf-*` / guardian agent may declare `soul: docs/agents/souls/<name>.md`
([[adr-02-harness]] rule 8). On dispatch, **prepend that file** to the node
prompt when the host does not load `soul:` natively (Cursor/Grok always;
Kimi/Claude if frontmatter is ignored). Soul is voice only — YAML contract
and law links in the agent file win.

## Shared invariants (all runtimes)

1. YAML final-message contracts — never prose handoffs between phases.
2. Dead / garbage node → phase abort (`hunter-failed`, …).
3. Builders create their own git worktrees; bard merges path-disjoint slices.
4. Post-bard: `guardian-dispatch --bundle <baseRef>` (adr-03 rule 10) + `assertion-review` when assertions moved.
5. `bin/kwf-deps` path: `docs/skills/triage-and-fix/bin/kwf-deps` from repo root.
