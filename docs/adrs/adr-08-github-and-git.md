---
title: adr-08-github-and-git
type: adr
status: active
created: 2026-07-10
tags: [adr, github, git]
---

# ADR-08 — GitHub and git

Rules only; content lives in [[GH]].

1. Owner is `kodexArg`. Remote and `gh` default owner follow that account.
2. `main` is integration, not production. 
3. `prod` is the production branch. 
4. Direct push to `main` and `prod` is allowed only as `kodexArg`. All other work uses feature branches and pull requests.
5. Issues and PRs are the collaboration surface — no silent long-lived private workstreams that skip them when the change is shared or lands on `main`/`prod`. [[adr-19-issue-worktree-pr]] makes both mandatory per change: every change opens an issue first and reaches `main` only through a PR.
6. Feature PRs target `main`. Promotions to production target `prod` (from `main` or an agreed release head). Detail: [[GH]].
7. Labels are only the fixed set in [[GH]].
8. Release git tags are semver `v*`, cut from `prod` only ([[GH]]).
9. CI/OIDC trust for deploy: dev ← `main`, prod ← `prod` ([[INFRASTRUCTURE]], [[GH]]).
