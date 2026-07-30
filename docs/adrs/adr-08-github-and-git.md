---
title: adr-08-github-and-git
type: adr
status: active
created: 2026-07-10
tags: [adr, github, git]
---

# ADR-08 — GitHub and git

Rules only; content lives in [[GH]].

1. The owning account is a per-repository fact, recorded in [[GH]] — not a constant of this doctrine. Remote and `gh` default owner follow whichever account [[GH]] names. For this repository that account is `jereezquerro92`; `kodexArg` owns the template this project was spawned from, and owning the template grants no authority over a project built on it ([[adr-48-derived-project-deploy-identity]] rule 4).
2. `main` is integration, not production. 
3. `prod` is the production branch. 
4. Direct push to `main` and `prod` is allowed only as the owning account of rule 1. All other work uses feature branches and pull requests.
5. Issues and PRs are the collaboration surface — no silent long-lived private workstreams that skip them when the change is shared or lands on `main`/`prod`. [[adr-19-issue-worktree-pr]] makes both mandatory per change: every change opens an issue first and reaches `main` only through a PR.
6. Feature PRs target `main`. Promotions to production target `prod` (from `main` or an agreed release head). Detail: [[GH]].
7. Labels are only the fixed set in [[GH]].
8. Release git tags are semver `v*`, cut from `prod` only ([[GH]]).
9. CI/OIDC trust for deploy: dev ← `main`, prod ← `prod` ([[INFRASTRUCTURE]], [[GH]]).
10. Owner override (2026-07-30, given in conversation, issue #52): rules 1 and 4 were edited in place — not superseded — to make the owning account a per-repository fact. This is the express-consent path of [[adr-00-adr-doctrine]] rule 4(b), taken because a supersession of this ADR would have emptied rules 2–9 to change one clause. The owner's stated ground: this repository is theirs, built on `kodexArg`'s template. The consent is bounded to that edit; it grants no wider exception to the supersession doctrine, here or anywhere else.
