---
title: adr-49-feedlot-campo-dedicated-rds
type: adr
category: devops
use_case: provisioning or changing this project's production database, pointing DB settings or secrets at an RDS instance, weighing shared-vs-dedicated placement
created: 2026-07-31
modified: 2026-08-02
tags: [adr, infrastructure, aws, rds, divergence]
---

# ADR-49 — feedlot-campo's dedicated RDS instance

## CONTEXT

> This project's production database is its own RDS instance, by explicit owner directive — a standing, recorded divergence from the shared-instance default [[BD]] prescribes, made through the divergence vehicle [[adr-02-initial-stack]] rule 5 requires.

## ASSERTIONS

1. `alvs-feedlot-campo`'s production database is a **dedicated** RDS instance, `alvs-prod-feedlot-campo-pg` — PostgreSQL 17.9, `db.t4g.micro`, single-AZ, 20 GB gp3, isolated subnets, never publicly reachable — not the shared `alvs-prod-pg` instance [[BD]] otherwise prescribes per project. This is a standing, owner-directed divergence, not a template default and not this project inventing its own infrastructure pattern.
2. The ground for the divergence is an explicit owner directive, given in conversation on 2026-07-31: this project gets its own instance. It is not derived from mirroring any sibling project's shape — the sibling actually mirrored during this project's bring-up, `alvs-financial-gateway`, is itself on the shared legacy `alvs-prod-pg` (discovered live, not assumed), so "dedicated" here is the owner's choice for this project specifically, overriding the mirror-sibling default for this one dimension only.
3. This ADR settles nothing about any other project's database placement. [[BD]]'s general prose — one project per shared instance as the template default — stands unchanged for projects the owner has not directed otherwise; this is a per-project exception recorded here and in [[BD]].
4. The network security group is shared infrastructure and stays shared. `sg-0c6f4c16f86f7a2b3` (`alvs-prod-rds-sg`) already fronts `alvs-prod-astro-drf-aws-pg` and the legacy `alvs-prod-pg`; reusing it for `alvs-prod-feedlot-campo-pg` is a network-level convenience with no bearing on rule 1 — the SG being shared does not make the instance shared.
5. Full identifiers, endpoint, and provisioning record live in [[INVENTORY]]'s `feedlot-campo` section, never here ([[adr-00-adr-doctrine]] rule 1).

## FORBIDDEN

- **NEVER** point this project's production database settings or secrets at the shared `alvs-prod-pg` (rule 1). The dedicated instance is an owner directive; quietly rejoining the shared instance would undo a standing decision without its owner.
- **NEVER** read rule 1 as a new template default (rule 3). Other projects keep [[BD]]'s shared-instance prescription until their owner directs otherwise.

## REJECTED

- **The shared `alvs-prod-pg` instance for this project** — the template default [[BD]] prescribes per project. Lost to the explicit owner directive of 2026-07-31 (rule 2). It would reopen only by a new owner decision, recorded here.
- **Deriving the placement from the mirrored sibling** — `alvs-financial-gateway` was the live mirror during bring-up, and it sits on the shared legacy instance; following it would have contradicted the owner's directive. Rejected because live sibling state describes the sibling, not this project's decision.

## RELATED

### related adrs

- [[docs/adrs/adr-02-initial-stack]] — rule 5, the requirement that an infrastructure divergence arrive as its own ADR
- [[docs/adrs/adr-48-derived-project-deploy-identity]] — rule 6, the inventory discipline the provisioning record follows

### history

- [[docs/obsolete/adr-12-ephemeral-run]] — the retired reference-run doctrine whose rule 4 set the precedent of a dedicated instance as a recorded exception

### related files

- [[docs/BD]] — the shared-instance default this ADR diverges from, and this project's dedicated-instance record
- [[docs/INVENTORY]] — the provisioned identifiers and endpoint
