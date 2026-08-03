---
title: adr-48-derived-project-deploy-identity
type: adr
status: active
created: 2026-07-30
tags: [infrastructure, github, oidc, deploy, identity]
---

# ADR-48 — the derived project's deploy identity

Rules only; content lives in [[GH]], [[INFRASTRUCTURE]], [[VARIABLES]]. This ADR adds to [[adr-08-github-and-git]] and [[adr-23-oidc-immutable-subject-claim]] (issue #48). It is a doctrine addition and supersedes nothing: what it settles is the case those ADRs did not contemplate — a project spawned from the template, living under a different owner, whose pipeline was inherited along with the code.

1. A deploy target is repository configuration, never a committed literal. The AWS account, deploy role, project slug, cluster, subnets, security group, and secret ARNs a deploy workflow uses are read at run time from that repository's own GitHub Actions variables. Typing any of them into a workflow file is a defect — not for secrecy (none of them is a secret), but because a committed value is inherited by every repo spawned from the template, and an inherited value points at the parent's infrastructure.

2. A deploy whose target is not configured fails closed, before authenticating. The workflow's first job verifies every required variable is set and hard-fails naming those that are not; no job may assume a role, push an image, register a task definition, or run a migration ahead of that check. A deploy blocked only by a mismatched credential is not a control — it is an accident that a later change can undo.

3. A project owns its identity, never a sibling's. A repo spawned from the template inherits the pipeline's *shape* and nothing about *where it deploys*: no account, no role, no cluster, no network, no secret path, and no inventory. Until a project's own resources exist, the correct and expected state is the fail-closed one of rule 2 — never a target borrowed from the project it was copied from.

4. The owning account is a per-repository fact, and [[GH]] is the document that records it — settled in [[adr-08-github-and-git]] rules 1 and 4 under the owner override recorded as its rule 10 (issue #52). Owning the template a project was spawned from grants no authority over the project. Everything else adr-08 rules — `main` is integration, `prod` is production, and only the owning `gh` identity pushes those lines ([[adr-19-issue-worktree-pr]] rule 3) — binds unchanged and was never in question.

5. A change of owner or repository rotates the OIDC identity, and both directions are re-derived. The immutable-subject obligation of [[adr-23-oidc-immutable-subject-claim]] rules 1–2 binds the derived project as it binds the template: the live prefix is read from GitHub, recorded in [[GH]], and every trust entry naming the repo is re-derived in the same batch. A prefix inherited from the template describes the template and is a defect in this repo.

6. Provisioning is a separate act from this rule set, and its record is [[INVENTORY]]. Nothing in a document, workflow, or test may assume this project has provisioned resources while [[INVENTORY]] records none — the same discipline [[adr-12-ephemeral-run]] rule 2 imposes on the template's own run, applied here to the case of no resources at all. Any change to rules 1–3 is semantic and MUST supersede this ADR ([[adr-00-adr-doctrine]] rule 4).
