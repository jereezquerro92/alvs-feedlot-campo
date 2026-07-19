---
title: adr-19-issue-worktree-pr
type: adr
status: active
created: 2026-07-15
tags: [adr, git, workflow, gh]
---

# ADR-19 — Issue → Worktree → PR

Rules only; the operational sequence, the tooling at each step, and the diagrams live in [[DEVELOPMENT-LOOP]] ([[adr-00-adr-doctrine]] rule 1). This ADR adds the mandatory shape of every change to [[adr-07-development-flow]] and [[adr-08-github-and-git]]; it narrows neither.

1. Every change enters through a `gh` issue — always, for everything, no matter how small. The issue is opened before the work, in this repo's own tracker ([[GH]]). A change with no issue is a change made by someone who did not read this ADR. This makes binding what [[adr-08-github-and-git]] rule 4 held as the default.

2. The pull request is the sole integration entry point. No change reaches `main` except by opening a PR and merging it; there is no direct hand-commit to `main` in the development flow. The worktree is optional — a plain feature branch → PR is the equal alternative; what is not optional is the PR.

3. Only the `gh`/kodexArg identity integrates, and in practice that is the agent — the sole holder of that credential. The merge to `main` is itself the kodexArg push that [[adr-08-github-and-git]] rule 3 authorizes; this ADR routes that push through a PR, it does not remove the permission. No human hand-merges outside the `gh` identity. No second-party review is implied: the PR is record + gate, and self-merge is valid ([[GH]]).

4. The PR is the gate: the guardian verdicts ([[adr-11-guardians]]) and the test suites must be green before merge. Enforcement is layered and the ADR states its limit honestly ([[adr-15-chatbot-two-tier]] rule 6 precedent — never overstate a control): this doctrine is the rule, a local `PreToolUse` hook is a bypassable nudge, and the only inviolable backstop is GitHub branch protection, which lives in the repo of the moment and is therefore not shipped by this template. No document may state the PR as an unbypassable gate.

5. Integration destroys the worktree — always and explicitly. On merge the worktree is removed with `git worktree remove` (the agent/`-p` path does not auto-clean, so the removal is never left to an interactive prompt) and the branch is deleted. No worktree and no branch outlives its PR, whether the PR merged or was abandoned.

6. Boilerplate. The flow's terms enter [[GLOSSARY]] before first use ([[adr-01-glossary-and-localization]]); the step-by-step rendering and the exact commands stay in [[DEVELOPMENT-LOOP]], never here; any change to rules 1–5 is semantic and MUST supersede this ADR ([[adr-00-adr-doctrine]] rule 4).
