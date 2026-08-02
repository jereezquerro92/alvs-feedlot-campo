---
title: adr-12-ephemeral-run
type: adr
status: active
created: 2026-07-11
tags: [adr, ephemeral, aws, teardown, run]
---

# ADR-12 — the ephemeral reference run

Rules only; content lives in [[INFRASTRUCTURE]], [[BD]], [[GH]], and [[VARIABLES]]. This ADR governs the template's own stage-3 reference deploy of project `astro-drf-aws`; it does not change multi-project doctrine.

1. This run deploys to `prod` only. No cloud dev environment exists here: `main` is the local development line and `prod` is the only branch that reaches AWS. OIDC deploy trust is scoped to `refs/heads/prod` only. The `dev ← main` pipeline stays doctrine for real projects and is out of scope for this run ([[INFRASTRUCTURE]], [[GH]], [[adr-08-github-and-git]]).
2. The infrastructure is born dead. No document, code path, test, or step may depend on any provisioned resource surviving. Resources may serve for testing after the final okay, but only ever as ephemeral.
3. Every created resource carries the mandatory tag set owned by [[INFRASTRUCTURE]] — `project`, `env`, `lifecycle`. A resource missing any of the three is a defect, not a resource of this run.
4. A dedicated ephemeral RDS instance is sanctioned here, diverging from the shared `alvs-prod-pg` precedent. [[adr-02-initial-stack]] rule 5 requires a new ADR for infrastructure divergence — this is it. Its specification and cost expectation are owned by [[BD]]; no local exception may widen the divergence.
5. The inventory is committed and authoritative. `docs/INVENTORY.md` is updated in the same batch as each resource's creation, in the format owned by [[INFRASTRUCTURE]]; teardown executes from it and verifies against the Resource Groups Tagging API.
6. Shared pre-existing ALVS resources are never destroyed — only this project's attachments to them. The set of shared resources and the removable attachments are owned by [[INFRASTRUCTURE]].
7. Teardown is total and user-gated. Every `lifecycle=ephemeral` resource and every one of this project's secrets is destroyed in the order and manner owned by [[INFRASTRUCTURE]] — secrets die last, irrecoverably. The run is closed only when the Tagging API confirms zero `lifecycle=ephemeral` resources remain. Teardown never runs without kodex's explicit go in the current conversation.
8. This ADR is the standing ruling every stage-3 phase assumes active. It rules the sibling findings on deploy scope and RDS cost; those are resolved in their own batches through the findings protocol, never by amending this ADR in place ([[adr-00-adr-doctrine]]).
