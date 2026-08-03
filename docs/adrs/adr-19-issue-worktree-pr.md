---
title: adr-19-issue-worktree-pr
type: adr
category: devops
use_case: starting any change, opening an issue or a PR, merging to main, cleaning up a branch or worktree
created: 2026-07-15
modified: 2026-08-02
tags: [adr, git, workflow, gh]
---

# ADR-19 — Issue → Worktree → PR

## CONTEXT

> Every change has the same shape: an issue opens it, a pull request integrates it, and the branch that carried it is destroyed. The worktree in the middle is optional; the issue and the PR are not.

## ASSERTIONS

1. Every change enters through a `gh` issue, opened before the work, in this repository's own tracker ([[GH]]) — for everything, no matter how small.
2. The pull request is the sole integration entry point. Nothing reaches `main` except by opening a PR and merging it; there is no hand-commit to `main` in the development flow. The worktree is an option, a plain feature branch its equal; the PR is neither.
3. Only the `gh` identity — the owning account [[adr-08-github-and-git]] rule 1 names for this repository — integrates, and in practice that is the agent, the sole holder of that credential. Routing the push through a PR does not remove the permission that rule grants. No second-party review is implied: the PR is record and gate, and self-merge is valid.
4. The PR is the gate: guardian verdicts ([[adr-11-guardians]]) and the test suites are green before merge. The enforcement is layered and its limit is stated honestly — this doctrine is the rule, a local `PreToolUse` hook is a bypassable nudge, and the only inviolable backstop is GitHub branch protection, which lives in the repository of the moment and is not shipped by this template.
5. Integration destroys the worktree. On merge it is removed with `git worktree remove` — explicitly, because the agent path does not auto-clean — and the branch is deleted. No worktree and no branch outlives its PR, merged or abandoned.
6. The flow's terms enter [[GLOSSARY]] before first use ([[adr-01-glossary-and-localization]]); the step-by-step rendering and the exact commands stay in [[DEVELOPMENT-LOOP]].

## FORBIDDEN

- **NEVER** start work before its issue exists (rule 1). The issue is where the change is stated and found again; opened afterwards it is a receipt, not a record.
- **NEVER** commit to `main` by hand (rule 2). The PR is the only entry, and a hand-commit leaves the change with no gate and no trail.
- **NEVER** merge with a red suite or an unresolved guardian verdict (rule 4). The gate exists at exactly that moment and nowhere else.
- **NEVER** state the PR as an unbypassable gate in any document (rule 4). Branch protection is the only backstop, this template does not ship it, and a control described as stronger than it is stops being checked.
- **NEVER** leave a worktree or branch alive after its PR closes (rule 5). Abandoned ones accumulate and the next reader cannot tell which are live.

## REJECTED

- **Mandatory worktrees** — every change isolated in its own worktree, the shape the ADR's own title still names. It lost to rule 2: the isolation is useful, the ceremony is not always worth it, and what actually protects `main` is the PR. A plain feature branch is the equal alternative.
- **Requiring a second-party review** — a human approver on every PR. Rejected because the `gh` identity is the only integrator and a required approval it cannot supply would block every change; the PR is record and gate, and self-merge is valid (rule 3).

## RELATED

### related adrs

- [[docs/adrs/adr-08-github-and-git]] — the branches, the owning account and the push permission rule 3 rides on
- [[docs/adrs/adr-07-development-flow]] — the gates a change passes between issue and PR
- [[docs/adrs/adr-11-guardians]] — the verdicts rule 4 requires green
- [[docs/adrs/adr-01-glossary-and-localization]] — a name decided before first use

### related files

- [[docs/DEVELOPMENT-LOOP]] — the sequence, the tooling and the exact commands
- [[docs/GH]] — the tracker, the labels and this repository's owning account
- [[docs/GLOSSARY]] — the flow's terms
