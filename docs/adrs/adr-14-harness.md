---
title: adr-14-harness
type: adr
category: harness
use_case: adding or removing a skill, reaching for a stack or AWS skill, resolving a skill that disagrees with a doc
created: 2026-07-13
modified: 2026-08-02
tags: [adr, harness, skills, agents]
---

# ADR-14 — the vendored skill harness

## CONTEXT

> The harness travels with the repository. Every required skill is a real copy inside it, and a skill is a procedure that never becomes a source of truth.

## ASSERTIONS

1. The required skill set is exactly what [[HARNESS]] lists. Adding a skill to the repo adds its row — name, why required, consumers — in the same batch; removing one removes the row first and the files second.
2. Every required skill is vendored as a self-contained real copy under `.claude/skills/<name>/`, mirrored at `skills/<name>/`, the two kept in sync. Nothing depends on a machine-global skill harness: a fresh clone exposes the full set with no external links ([[HARNESS]]).
3. The stack and DevOps skills are the sanctioned path for their domains, not optional aids — frontend through `kdx-astro-7`, backend through `kdx-django-6-drf`, AWS through the `kdx-aws-*` set. Vault `.md` is written through `obsidian-markdown`, go/no-go triage through `kdx-triage`, multi-step fan-out through `kdx-orchestrator` ([[AGENTS]]).
4. A skill reinforces the ABC gate and never replaces it: a skill-driven change still follows [[PRD]], complies with every ADR, and enters the backend zone only through [[API]] ([[adr-07-development-flow]]). Convenience waives neither the gate ([[AGENTS]]) nor a guardian verdict ([[adr-11-guardians]]).
5. Agents are part of the harness but are not skills. Their definitions and rules stay with `agents/` and [[adr-11-guardians]] rule 1; [[HARNESS]] records them for completeness only.
6. A skill carries no rule an ADR owns. Where a skill and a doc disagree, the doc wins ([[adr-00-adr-doctrine]] rule 1): the skill is the procedure, the doc is the truth.

## FORBIDDEN

- **NEVER** ship a skill with no [[HARNESS]] row, or a row with no skill (rule 1). An uninventoried skill is one nobody knows to update when its domain changes.
- **NEVER** point the harness at a machine-global skill directory (rule 2). A clone that works only on the machine that wrote it is not a harness.
- **NEVER** let a skill's procedure override a doc's rule (rule 6). The doc is the SSOT; the skill is how the work is done today.
- **NEVER** treat reaching for a skill as clearing the ABC gate (rule 4). The gate is checked per change, whatever tool performed it.

## REJECTED

- **Symlinking the machine-global harness** (`~/.agents/skills/`, `~/.claude/skills/`) — it would have kept one copy per machine and updated every project at once. It lost because a repo whose harness lives outside it cannot be cloned into a working state, and the version a project was tested against would silently drift with the machine. Closed for as long as rule 2 stands.

## RELATED

### related adrs

- [[docs/adrs/adr-11-guardians]] — rule 1, which owns adding a guardian
- [[docs/adrs/adr-00-adr-doctrine]] — rule 1, the ordering rule 6 applies to skills
- [[docs/adrs/adr-07-development-flow]] — the gates rule 4 refuses to let a skill waive

### related files

- [[docs/HARNESS]] — the skill inventory, why each is required, and its consumers
- [[AGENTS]] — the ABC gate and the fan-out entry point
