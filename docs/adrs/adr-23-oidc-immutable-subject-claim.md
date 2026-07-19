---
title: adr-23-oidc-immutable-subject-claim
type: adr
status: active
created: 2026-07-19
tags: [adr, github, oidc, ci, infra]
---

# ADR-23 — immutable OIDC subject claims

Rules only; content lives in [[GH]] and [[INFRASTRUCTURE]]. This ADR adds to [[adr-08-github-and-git]] rule 9; it narrows nothing else and supersedes nothing (issue #1).

1. A CI/OIDC trust-policy `sub` entry for a GitHub repo created, renamed, or transferred after GitHub's immutable-subject cutoff MUST use the immutable subject format — owner and repository numeric IDs embedded. A name-only entry for such a repo is a defect: it can never match, and the deploy is denied. The format, the cutoff date, the lookup command, and this repo's live values are owned by [[GH]].

2. Recreating, renaming, or transferring a repo rotates its OIDC identity. Every trust entry naming that repo MUST be re-derived in the same batch as the change, and where the trust lives on a shared role, the mutation is recorded under the inventory discipline of [[adr-12-ephemeral-run]].

3. This is a doctrine addition, not a reversal: deploy refs, the branch→env mapping, and who may push ([[adr-08-github-and-git]]) are untouched. Any change to rules 1–2 is semantic and MUST supersede this ADR ([[adr-00-adr-doctrine]]).
