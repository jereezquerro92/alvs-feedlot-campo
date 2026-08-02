---
title: adr-07-development-flow
type: adr
category: harness
use_case: starting any new feature or backend change, deciding whether the BDD/API/TDD gates apply, checking whether to enter or exit the backend zone
created: 2026-07-10
modified: 2026-08-02
tags: [adr, workflow, bdd, tdd, api]
---

# ADR-07 — the development flow

## CONTEXT

> Every change climbs the same three gates in the same order: [[BDD]] before code, [[API]] before backend work, the checkpoint before leaving the backend zone. [[DEVELOPMENT-LOOP]] carries the operational rendering; this ADR makes the order invariant.

## ASSERTIONS

1. User-facing work is bound by the [[BDD]] gate: its [[BDD]] entry exists before its code does.
2. The backend zone is entered only through [[API]], and a need is served by an endpoint already declared there before a new one is considered.
3. A new endpoint's row lands in [[API]] before its code, and the code that follows is born through the [[TDD]] flow ([[adr-03-api-and-backend]]).
4. The backend zone is exited only through the checkpoint — does [[API]] solve the need? Its rendering as a loop lives in [[DEVELOPMENT-LOOP]].
5. What this ADR makes invariant is the order of the gates: [[BDD]] before code, [[API]] before backend work, the checkpoint before leaving the backend zone. The intermediate steps are owned by [[BDD]], [[TDD]], and the stack docs.
6. Two distinct claims: full activation — every feature must enter through this loop — lands only when the base template is finished (it is). Gate applicability is immediate — each gate ([[BDD]], [[API]], [[TDD]]) already binds now, wherever its subject exists, including the template's own construction.

## FORBIDDEN

- **NEVER** write user-facing code before its [[BDD]] entry exists (rule 1). The gate exists so the behavior is specified before it is built.
- **NEVER** enter the backend zone by a door other than [[API]] (rule 2). A need first checks whether an existing endpoint already serves it.
- **NEVER** write a model or a test before the endpoint's row lands in [[API]] (rule 3, [[adr-03-api-and-backend]] rule 2). The contract precedes the code that serves it.
- **NEVER** leave the backend zone without passing the does-[[API]]-solve-the-need checkpoint (rule 4). Skipping it is how an endpoint ships that never actually closed the loop back to the feature that needed it.

## RELATED

### related adrs

- [[docs/adrs/adr-03-api-and-backend]] — the API-before-code sequence this ADR's rule 3 cites directly
- [[docs/adrs/adr-19-issue-worktree-pr]] — the same before-code discipline applied to git, not the API

### related files

- [[docs/DEVELOPMENT-LOOP]] — the operational rendering: exact sequence and tool/skill per step
- [[docs/BDD]] — the user-facing gate
- [[docs/TDD]] — the backend build flow
- [[AGENTS]] — where this loop is indexed and opened at the start of any code
