---
title: BD
type: reference
status: active
created: 2026-07-10
tags: [harness, database]
---

# BD

Database reference for the template. Engine: **PostgreSQL 17.9** (pin in [[REQUIREMENTS]]). Network placement, security groups, and bastion → [[INFRASTRUCTURE]]. Credentials as variables → [[VARIABLES]].

> [!note]
> Environments are **dev and prod only — no staging tier** in this account.

## prod

- RDS PostgreSQL **17.9**, instance `alvs-prod-pg`, class `db.t4g.micro`, **single-AZ**, in the isolated subnets ([[INFRASTRUCTURE]]).
- App credentials via Secrets Manager `alvs/prod/<project>/db` — JSON keys `host`, `port`, `dbname`, `username`, `password` — mapped to the discrete `DB_*` env vars ([[VARIABLES]]).
- Admin access **only** through the EICE bastion tunnel ([[INFRASTRUCTURE]]). The instance is never publicly reachable.

## dev (cloud)

- Identical pattern on `alvs-dev-pg`; secret `alvs/dev/<project>/db`.

## Ephemeral run RDS (reference deploy)

Ruled by [[adr-12-ephemeral-run]]. The template's own run diverges from the shared `alvs-prod-pg` precedent above: it gets a **dedicated instance, born dead** — the sanctioned divergence (no project shares this DB, and it is destroyed at teardown).

- Instance `alvs-prod-astro-drf-aws-pg` (name frozen at B1), PostgreSQL 17.9, `db.t4g.micro`, single-AZ, 20 GB gp3, isolated subnets, SG `alvs-prod-rds-sg`, never publicly reachable.
- **Deletion protection off, no final snapshot** — ephemeral ([[INFRASTRUCTURE]] teardown order).
- Database name `app` — the slug's hyphens stay out of SQL.
- **Cost expectation:** AWS free tier is **not** available on the ALVS account; `db.t4g.micro` is the chosen class either way (cost discipline, `kdx-aws-cost`). Cost containment is the tag set + Phase E teardown, never instance survival.

## local (dev)

- Local PostgreSQL 17 (container or native), configured through the same discrete `DB_*` contract.
- Preferred container path: Compose service `db` via [[DOCKER]] (`docker compose --profile db up -d`).
- The code never knows which environment it's in — only the connection variables change.

## Rules

> [!important]
> **Django migrations are the ONLY schema mechanism.** No manual DDL, no external migration tools.

- One database per project per env.
- The cache table from [[CACHE]] lives in this same database — no separate cache store, Redis is prohibited.
- Engine version is pinned in [[REQUIREMENTS]]; re-pin follows that doc's policy.

## Migration execution points

- **Local:** the compose `backend` service runs `manage.py migrate` at startup ([[DOCKER]]) — dev convenience, single task, no race.
- **Cloud:** CI runs `migrate` as a **one-off ECS task before the service update**, never inside the service containers at startup — parallel tasks racing the same DDL is the failure mode this rule exists to prevent ([[INFRASTRUCTURE]] CI/CD).

## User identity

- User rows key on the Cognito `sub` claim — immutable, never recycled ([[GLOSSARY]]).
- User profile field names mirror Cognito standard attributes (`email`, `given_name`, `family_name`, …) so DRF serializers and Cognito claims share names with zero mapping. Auth doctrine: [[AUTH]].
