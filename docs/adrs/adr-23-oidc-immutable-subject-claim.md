---
title: adr-23-oidc-immutable-subject-claim
type: adr
category: devops
use_case: writing or editing an OIDC trust policy, renaming or transferring a repository, debugging a deploy denied at role assumption
created: 2026-07-19
modified: 2026-08-02
tags: [adr, github, oidc, ci, infra]
---

# ADR-23 — immutable OIDC subject claims

## CONTEXT

> A trust policy that names a repository by name alone can never match one created, renamed or transferred after GitHub's immutable-subject cutoff. Those entries carry the numeric owner and repository IDs, and they are re-derived whenever the repository's identity moves.

## ASSERTIONS

1. A CI/OIDC trust-policy `sub` entry for a repository created, renamed or transferred after GitHub's immutable-subject cutoff uses the immutable subject format, with the owner and repository numeric IDs embedded. A name-only entry for such a repository is a defect: it can never match, and the deploy is denied. The format, the cutoff date, the lookup command and this repository's live values are owned by [[GH]].
2. Recreating, renaming or transferring a repository rotates its OIDC identity. Every trust entry naming that repository is re-derived in the same batch as the change, and where the trust lives on a shared role the mutation is recorded in [[INVENTORY]] under the discipline [[INFRASTRUCTURE]] owns.
3. Deploy refs, the branch→env mapping and who may push ([[adr-08-github-and-git]]) are untouched by this ADR; it adds a format requirement to rule 9 and nothing else.

## FORBIDDEN

- **NEVER** write a name-only `sub` entry for a post-cutoff repository (rule 1). It cannot match, so the deploy fails at role assumption with an error that reads like a permissions problem and is not one.
- **NEVER** rename or transfer a repository without re-deriving its trust entries in the same batch (rule 2). The old prefix keeps matching nothing, and the break surfaces at the next deploy instead of at the change that caused it.
- **NEVER** copy a trust prefix from another repository (rule 1). The IDs are that repository's identity; an inherited prefix points at whoever it was copied from ([[adr-48-derived-project-deploy-identity]] rule 5).

## REJECTED

- **Wildcarding the subject to survive renames** — a `sub` pattern loose enough that a renamed repository still matches. Rejected because the looseness is the whole risk: a wildcard that tolerates a rename also tolerates a repository nobody intended, and the trust policy is the only thing standing between an OIDC token and the deploy role.

## RELATED

### related adrs

- [[docs/adrs/adr-08-github-and-git]] — rule 9, the branch→env deploy trust this formats
- [[docs/adrs/adr-48-derived-project-deploy-identity]] — rule 5, the same obligation on a project spawned from the template

### related files

- [[docs/GH]] — the subject format, the cutoff, the lookup command, the live values
- [[docs/INFRASTRUCTURE]] — the roles the trust lives on and the recording discipline
- [[docs/INVENTORY]] — where a shared-role mutation is recorded
