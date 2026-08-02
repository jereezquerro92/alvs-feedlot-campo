---
title: adr-08-github-and-git
type: adr
category: devops
use_case: pushing to main or prod, opening a PR, cutting a release tag, wiring CI/OIDC deploy trust, checking who the owning account is
created: 2026-07-10
modified: 2026-08-02
tags: [adr, github, git]
---

# ADR-08 — GitHub and git

## CONTEXT

> `main` is integration, `prod` is production, and only the owning account of this repository pushes either line directly. Everything else is a branch and a PR.

## ASSERTIONS

1. The owning account is a per-repository fact, recorded in [[GH]] — not a constant of this doctrine. Remote and `gh` default owner follow whichever account [[GH]] names. For this repository that account is `jereezquerro92`; `kodexArg` owns the template this project was spawned from, and owning the template grants no authority over a project built on it ([[adr-48-derived-project-deploy-identity]] rule 4).
2. `main` is integration, not production.
3. `prod` is the production branch.
4. Direct push to `main` and `prod` is allowed only as the owning account of rule 1. All other work uses feature branches and pull requests.
5. Issues and PRs are the collaboration surface — no silent long-lived private workstreams that skip them when the change is shared or lands on `main`/`prod`. [[adr-19-issue-worktree-pr]] makes both mandatory per change: every change opens an issue first and reaches `main` only through a PR.
6. Feature PRs target `main`. Promotions to production target `prod` (from `main` or an agreed release head). Detail: [[GH]].
7. Labels are only the fixed set in [[GH]].
8. Release git tags are semver `v*`, cut from `prod` only ([[GH]]).
9. CI/OIDC trust for deploy: dev ← `main`, prod ← `prod` ([[INFRASTRUCTURE]], [[GH]]).

## FORBIDDEN

- **NEVER** push directly to `main` or `prod` as any account other than the owner of rule 1 (rule 4). Every other line of work is a branch and a PR.
- **NEVER** carry a shared change on a silent long-lived branch that skips the issue/PR surface (rule 5, [[adr-19-issue-worktree-pr]]). A change with no issue is a change nobody outside its author can find.
- **NEVER** use a label outside the fixed set in [[GH]] (rule 7). A one-off label is a second taxonomy nobody else knows to filter by.
- **NEVER** cut a release tag from a branch other than `prod` (rule 8). A tag cut from `main` describes integration state, not what actually shipped.

## REJECTED

- **A constant owning account (`kodexArg`) baked into this doctrine** — rules 1 and 4 named `kodexArg` as the owner until 2026-07-30. Retired by owner override (issue #52, express-consent path of [[adr-00-adr-doctrine]] rule 8) because a project spawned from the template has its own owner, and owning the template a project was built on grants no authority over the project itself ([[adr-48-derived-project-deploy-identity]] rule 4). The consent was bounded to this edit; it opened no wider exception to how a policy changes elsewhere. It would reopen only if this template's own reference repository needed a rule naming itself specifically.

## RELATED

### related adrs

- [[docs/adrs/adr-19-issue-worktree-pr]] — the mandatory issue→PR shape rule 5 requires
- [[docs/adrs/adr-48-derived-project-deploy-identity]] — rule 4, the ground rule 1's per-repository fact rests on
- [[docs/adrs/adr-23-oidc-immutable-subject-claim]] — the OIDC trust format rule 9's deploy trust must use

### related files

- [[docs/GH]] — the owning account, labels, and branch/tag detail this ADR gives force to
- [[docs/INFRASTRUCTURE]] — the deploy trust rule 9 wires into
