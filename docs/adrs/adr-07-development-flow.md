---
title: adr-07-development-flow
type: adr
status: active
created: 2026-07-10
tags: [adr, workflow, bdd, tdd, api]
---

# ADR-07 — the development flow

Rules only. This ADR gives force to the loop defined in [[DEVELOPMENT-LOOP]] and indexed in [[AGENTS]]; that same file carries its operational rendering — the sequence and the tool/skill at each step ([[adr-00-adr-doctrine]] rule 1).

1. User-facing work is bound by the [[BDD]] gate: its [[BDD]] entry exists before its code does.
2. The backend zone is entered only through [[API]], and a need is served by an endpoint already declared there before a new one is considered.
3. A new endpoint's row lands in [[API]] before its code, and the code that follows is born through the [[TDD]] flow ([[adr-03-api-and-backend]]).
4. The backend zone is exited only through the checkpoint — does [[API]] solve the need? Its rendering as a loop lives in [[DEVELOPMENT-LOOP]].
5. What this ADR makes invariant is the order of the gates: [[BDD]] before code, [[API]] before backend work, the checkpoint before leaving the backend zone. The intermediate steps are owned by [[BDD]], [[TDD]], and the stack docs.
6. Two distinct claims: full activation — every feature must enter through this loop — lands only when the base template is finished (it is). Gate applicability is immediate — each gate ([[BDD]], [[API]], [[TDD]]) already binds now, wherever its subject exists, including the template's own construction.
