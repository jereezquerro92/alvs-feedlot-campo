---
title: adr-14-harness
type: adr
status: active
created: 2026-07-13
tags: [adr, harness, skills, agents]
---

# ADR-14 — the vendored skill harness

Rules only; the skill inventory and the reasons live in [[HARNESS]].

1. The required skill set is exactly what [[HARNESS]] lists. A skill absent from that table is not part of the template's harness; adding one to the repo means adding its row — name, why required, consumers — first, in the same batch. Removing one removes the row first, the files second ([[adr-00-adr-doctrine]] discipline, applied to skills).
2. Every required skill is vendored as a real copy, self-contained. It lives under `.claude/skills/<name>/` (git-tracked — the home the harness loads) and is mirrored under `skills/<name>/`; the two stay in sync. The template never depends on the machine-global symlink harness (`~/.agents/skills/`, `~/.claude/skills/`) — a fresh clone on any machine exposes the full set with no external links ([[HARNESS]]).
3. The stack and DevOps skills are the sanctioned path for their domains, not optional aids: frontend through `kdx-astro-7` ([[adr-04-frontend-and-design-system]]), backend through `kdx-django-6-drf` ([[adr-03-api-and-backend]]), AWS through the `kdx-aws-*` set ([[INFRASTRUCTURE]], [[adr-02-initial-stack]], [[adr-06-cache]]). Vault `.md` is written through `obsidian-markdown`; go/no-go triage through `kdx-triage`; multi-step fan-out through `kdx-orchestrator` ([[AGENTS]]).
4. Skills reinforce the ABC gate; they do not replace it. Every skill-driven change still follows [[PRD]], complies with the active ADRs, and enters the backend zone only through [[API]] ([[adr-07-development-flow]]). A skill's convenience never waives the ABC ([[AGENTS]]) or a guardian verdict ([[adr-11-guardians]]).
5. Agents are part of the harness but are not skills. Their SSOT and rules stay with `agents/` and [[adr-11-guardians]]; [[HARNESS]] records them for completeness only. Adding a guardian still requires its [[GLOSSARY]] row and a supersession, never a change here.
6. Skills carry no information ADRs would otherwise own. Where a skill and a doc disagree on a rule, the ADR-backed doc wins ([[adr-00-adr-doctrine]]); a skill is a procedure, the SSOT doc is the truth.
