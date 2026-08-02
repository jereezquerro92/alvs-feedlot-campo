---
title: GH
type: reference
category: devops
use_case: branching, opening a PR, tagging a release, or checking who owns this repo
created: 2026-07-10
modified: 2026-08-02
tags: [doc, harness, github, git]
---

# GH — GitHub + git for this template

Owner of **this** repository: **`jereezquerro92`** — `jereezquerro92/alvs-feedlot-campo`. Repo protocol: SSH. CLI: `gh` (used directly). Ruled by [[adr-08-github-and-git]], whose rule 1 makes the owning account a per-repository fact that **this line is the record of**. `kodexArg` owns the template this project was spawned from and holds no authority here ([[adr-48-derived-project-deploy-identity]] rule 4; the in-place edit is recorded as adr-08 rule 10, issue #52). Everything else adr-08 rules — the branch roles, who may push them — binds unchanged and applies to the account named above.

## Branches

| Branch | Role |
|---|---|
| **`main`** | Integration / default development. Feature PRs merge here. |
| **`prod`** | **Production.** Not `main`. Promote only from `main` (PR → `prod`). |

Forbidden as production name: treating `main` as live. Forbidden branch name for default: `master` ([[GLOSSARY]]).

## Who may push

- **Direct push to `main` and `prod`:** the owning account only — **`jereezquerro92`** here ([[adr-48-derived-project-deploy-identity]] rule 4).
- Everyone else (agents, collaborators): **branches + PRs**. No direct push to protected lines.

## How we work

1. **Issues** for work tracking — open early, close with PR. An issue states the behavior before the code exists ([[adr-07-development-flow]] rule 1) and links liberally — governing ADRs, specs, code, related issues — so none is orphaned for want of a link graph. The repository ships no issue template.
2. **PRs** for every change that lands on `main` (and every promote to `prod`).
3. Agents open branches / PRs; they do not force-push `main`/`prod` as another identity.
4. Base of feature PRs: **`main`**. Base of release/promote PRs: **`prod`** (head = `main` or release branch).

## Labels (issues + PRs) — fixed set

Create only these; do not invent free-form labels.

| Label | Use |
|---|---|
| `bug` | Defect |
| `feat` | New capability |
| `chore` | Tooling, deps, noise cleanup |
| `docs` | Documentation / harness docs |
| `harness` | Skills, hooks, ADRs, agent config |
| `infra` | AWS, CI, deploy |
| `blocked` | Waiting on decision/input |

One primary type label per issue/PR; add `blocked` only when stuck.

## Git tags (releases)

- Format: **`vMAJOR.MINOR.PATCH`** (semver).
- Cut tags **from `prod` only** after a promote lands.
- Optional prerelease: `vX.Y.Z-rc.N` still from `prod` (or a short-lived release branch merged to `prod` first).

## CI / deploy refs

- **dev** pipelines / OIDC trust: `refs/heads/main` (and PR checks).
- **prod** pipelines / OIDC trust: `refs/heads/prod` (and tags `v*` if used).
- Detail for AWS roles: [[INFRASTRUCTURE]].

### OIDC subject format — immutable IDs

Ruled by [[adr-23-oidc-immutable-subject-claim]]. GitHub repos **created, renamed, or transferred after 2026-07-15** emit their Actions OIDC `sub` claim in the **immutable subject format**, which appends the owner and repository numeric IDs — permanent identifiers a delete-and-recreate cannot reuse. There is no opt-out for such repos ([changelog 2026-04-23](https://github.blog/changelog/2026-04-23-immutable-subject-claims-for-github-actions-oidc-tokens/)).

| | `sub` format |
|---|---|
| Classic (pre-cutoff repos) | `repo:OWNER/REPO:ref:refs/heads/BRANCH` |
| Immutable (post-cutoff repos) | `repo:OWNER@OWNER-ID/REPO@REPO-ID:ref:refs/heads/BRANCH` |

Consequences that bind this template and every project spawned from it:

- An AWS trust-policy `sub` entry for a post-cutoff repo MUST use the immutable format; a name-only entry never matches and STS denies `AssumeRoleWithWebIdentity` with `Not authorized to perform sts:AssumeRoleWithWebIdentity`.
- Deleting and recreating a repo rotates its repo ID, so every trust entry for it must be re-derived — the name-only entry it had before is dead. The same rotation happens when a project is spawned under a new owner: it is a different repo with a different ID, so it gets a different `sub` ([[adr-48-derived-project-deploy-identity]] rule 5).
- Read a repo's live prefix with `gh api repos/OWNER/REPO/actions/oidc/customization/sub` (`sub_claim_prefix`).

  **This repo** (`jereezquerro92/alvs-feedlot-campo`, created 2026-07-21 — post-cutoff, immutable, verified live 2026-07-30):

  ```
  repo:jereezquerro92@287022789/alvs-feedlot-campo@1307918497:ref:refs/heads/prod
  ```

  That is the only `sub` an AWS trust policy may accept for this project's `prod` deploys. The template's own prefix — `repo:kodexArg@47777332/astro-drf-aws@1305504992` — describes the template, matches nothing emitted here, and is recorded only so it is never mistaken for this one.
- Repos born before the cutoff keep the classic format until they are recreated, renamed, or transferred — then they flip and their trust entries must follow.

> [!note] The template's reference run
> For the template's own stage-3 run the `dev ← main` pipeline was **out of scope**: `main` was the local development line, `prod` the only branch reaching AWS, and OIDC deploy trust existed for `refs/heads/prod` only. The `dev ← main` trust above is doctrine for a project that provisions its own resources ([[INFRASTRUCTURE]]).
