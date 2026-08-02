---
title: adr-48-derived-project-deploy-identity
type: adr
category: devops
use_case: editing a deploy workflow, configuring a repository's deploy variables, spawning a project from the template, diagnosing a deploy that fails before authenticating
created: 2026-07-30
modified: 2026-08-02
tags: [adr, infrastructure, github, oidc, deploy, identity]
---

# ADR-48 — the derived project's deploy identity

## CONTEXT

> A project spawned from the template inherits the pipeline's shape and nothing about where it deploys. Every target is repository configuration read at run time, and a deploy with none configured fails closed rather than reaching for the parent's infrastructure.

## ASSERTIONS

1. A deploy target is repository configuration, never a committed literal. The AWS account, deploy role, project slug, cluster, subnets, security group and secret ARNs a workflow uses are read at run time from that repository's own GitHub Actions variables. Typing any of them into a workflow file is a defect — not for secrecy, none of them is a secret, but because a committed value is inherited by every repo spawned from the template and points at the parent's infrastructure.
2. A deploy whose target is not configured fails closed, before authenticating. The workflow's first job verifies every required variable is set and hard-fails naming those that are not; no job assumes a role, pushes an image, registers a task definition or runs a migration ahead of that check.
3. A project owns its identity, never a sibling's. A spawned repo inherits no account, role, cluster, network, secret path or inventory. Until its own resources exist, the fail-closed state of rule 2 is the correct and expected one.
4. The owning account is a per-repository fact recorded in [[GH]] ([[adr-08-github-and-git]] rules 1 and 4). Owning the template a project was spawned from grants no authority over the project. Everything else adr-08 rules — `main` is integration, `prod` is production, and only the owning `gh` identity pushes those lines — binds unchanged.
5. A change of owner or repository rotates the OIDC identity and both directions are re-derived: the live prefix is read from GitHub, recorded in [[GH]], and every trust entry naming the repo is re-derived in the same batch ([[adr-23-oidc-immutable-subject-claim]] rules 1–2). A prefix inherited from the template describes the template.
6. Provisioning is a separate act and its record is [[INVENTORY]]. No document, workflow or test may assume this project has provisioned resources while [[INVENTORY]] records none.

## FORBIDDEN

- **NEVER** commit a deploy target into a workflow file (rule 1). The template copies it forward, and the copy aims a child project at its parent's account.
- **NEVER** assume a role or push an image before the configuration check (rule 2). A deploy blocked only by a mismatched credential is not a control; it is an accident a later change can undo.
- **NEVER** borrow a sibling project's account, role, cluster or secret path (rule 3). Fail-closed is the correct state until this project's own resources exist.
- **NEVER** carry the template's OIDC prefix into a derived repo (rule 5). It describes the template and can only ever deny this project's deploy.
- **NEVER** claim authority over a project because you own the template it came from (rule 4). The owning account is recorded per repository in [[GH]].
- **NEVER** write a document or test that assumes resources [[INVENTORY]] does not record (rule 6).

## REJECTED

- **Committing the deploy target as a default a project overrides** — the template's own account and cluster in the workflow, expected to be edited after spawning. Rejected because the edit is exactly what gets forgotten, and the failure mode is a child project deploying into its parent's account rather than an error.
- **Letting a missing variable fail at role assumption** — no pre-check, relying on AWS to deny. Rejected by rule 2: the denial is incidental, it names nothing useful, and a later credential change turns the accident into a successful wrong deploy.

## RELATED

### related adrs

- [[docs/adrs/adr-08-github-and-git]] — rules 1 and 4, the owning account as a per-repository fact
- [[docs/adrs/adr-23-oidc-immutable-subject-claim]] — rules 1–2, the subject format rule 5 re-derives
- [[docs/adrs/adr-19-issue-worktree-pr]] — rule 3, who integrates

### related files

- [[docs/GH]] — the owning account, the live OIDC prefix, the branches
- [[docs/INFRASTRUCTURE]] — the resources a deploy target names
- [[docs/INVENTORY]] — what this project has actually provisioned
- [[docs/VARIABLES]] — the variables a workflow reads
