---
title: ADR-49 — feedlot-campo's dedicated RDS instance
type: adr
status: active
created: 2026-07-31
tags: [infrastructure, aws, rds, divergence]
---

# ADR-49 — feedlot-campo's dedicated RDS instance

Rules only; content lives in [[BD]] and [[INVENTORY]]. This ADR is the divergence vehicle [[adr-02-initial-stack]] rule 5 requires before diverging from the shared `alvs-prod-pg` precedent, following the exact precedent [[adr-12-ephemeral-run]] rule 4 set for the template's own reference run. It supersedes nothing.

1. `alvs-feedlot-campo`'s production database is a **dedicated** RDS instance, `alvs-prod-feedlot-campo-pg` — PostgreSQL 17.9, `db.t4g.micro`, single-AZ, 20 GB gp3, isolated subnets, never publicly reachable — not the shared `alvs-prod-pg` instance [[BD]] otherwise prescribes per project. This is a standing, owner-directed divergence, not a template default and not this project inventing its own infrastructure pattern.

2. The ground for the divergence is an explicit owner directive, given in conversation on 2026-07-31: this project gets its own instance. It is not derived from mirroring any sibling project's shape — the sibling actually mirrored during this project's bring-up, `alvs-financial-gateway`, is itself on the shared legacy `alvs-prod-pg` (discovered live, not assumed), so "dedicated" here is the owner's choice for this project specifically, overriding the mirror-sibling default for this one dimension only.

3. This ADR settles nothing about any other project's database placement. `docs/BD.md`'s general prose — one project per shared instance as the template default — stands unchanged for projects the owner has not directed otherwise; this is a per-project exception recorded here and in [[BD]], exactly as [[adr-12-ephemeral-run]] rule 4 recorded the template's own reference run as an exception rather than rewriting the shared-instance default.

4. The network security group is shared infrastructure and stays shared. `sg-0c6f4c16f86f7a2b3` (`alvs-prod-rds-sg`) already fronts `alvs-prod-astro-drf-aws-pg` and the legacy `alvs-prod-pg`; reusing it for `alvs-prod-feedlot-campo-pg` is a network-level convenience with no bearing on rule 1 — the SG being shared does not make the instance shared.

5. Full identifiers, endpoint, and provisioning record live in [[INVENTORY]]'s `feedlot-campo` section, not here (this ADR states the rule, never inlines the facts — [[adr-00-adr-doctrine]] rule 1). Any change to rules 1–4 is semantic and MUST supersede this ADR ([[adr-00-adr-doctrine]] rule 4).
