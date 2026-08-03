---
title: adr-07-development-flow
type: adr
category: harness
use_case: starting any new feature or backend change, deciding whether the API/TDD gates apply, checking whether to enter or exit the backend zone
created: 2026-07-10
modified: 2026-08-02
tags: [adr, workflow, tdd, api]
---

# ADR-07 — the development flow

## CONTEXT

> Two gates in one order: [[API]] before backend work, the checkpoint before leaving the backend zone. [[DEVELOPMENT-LOOP]] renders the steps; this ADR fixes the order.

## ASSERTIONS

1. User-facing work is specified before it is built: the behavior is agreed in the issue that opens the change ([[GH]]) before its code exists.
2. The backend zone is entered only through [[API]], and a need is served by an endpoint already declared there before a new one is considered.
3. What follows the row in [[API]] is [[adr-51-api-and-backend]] rules 2 and 6 — the contract before tests and models, the code born through [[TDD]]. This ADR adds nothing to them.
4. The backend zone is exited only through the checkpoint — does [[API]] solve the need?
5. The intermediate steps are owned by [[TDD]] and the stack docs; this ADR owns only the order.
6. Each gate binds now, wherever its subject exists, including the template's own construction.

## FORBIDDEN

- **NEVER** write user-facing code before its behavior is agreed in its issue (rule 1).
- **NEVER** enter the backend zone by a door other than [[API]] (rule 2).
- **NEVER** write a model or a test before the endpoint's row lands in [[API]] ([[adr-51-api-and-backend]] rule 2).
- **NEVER** leave the backend zone without passing the checkpoint (rule 4). Skipping it ships an endpoint that never closed the loop back to the feature needing it.

## REJECTED

- **Staged activation** — rule 6 held until 2026-08-02 that full activation waited on the base template being finished. The template is finished, so the condition is spent; the rule now states only that the gates bind.

## RELATED

### related adrs

- [[docs/adrs/adr-51-api-and-backend]] — rules 2 and 6, the owner of what rule 3 points at
- [[docs/adrs/adr-19-issue-worktree-pr]] — the same before-code discipline applied to git

### related files

- [[docs/DEVELOPMENT-LOOP]] — the operational rendering: sequence and tool per step
- [[docs/TDD]] — the backend build flow
- [[AGENTS]] — where this loop is indexed
