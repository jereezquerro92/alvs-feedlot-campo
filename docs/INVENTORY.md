---
title: INVENTORY
type: reference
status: active
created: 2026-07-11
tags: [infrastructure, aws, inventory, ephemeral]
---

# INVENTORY

The committed resource inventory for the `astro-drf-aws` stage-3 run. Every AWS resource this run touches has a row here, updated **in the same batch** as its creation ([[adr-12-ephemeral-run]] Article III). Phase E teardown executes from the `ephemeral` rows and verifies against the Resource Groups Tagging API; `shared` rows are never destroyed.

- Account `789650504128`, region `us-east-1`, profile `kodex` ([[INFRASTRUCTURE]]).
- `shared` = pre-existing ALVS resource, never mutated beyond this project's own attachments; `ephemeral` = created by this run, carries the mandatory tag set (`project=astro-drf-aws`, `env=prod`, `lifecycle=ephemeral`) and dies in Phase E.

> [!note] Provenance
> The `shared` section was seeded by B0 discovery (read-only, 2026-07-11). All identifiers below were confirmed to exist; zero mutations were made.

## Shared resources

| Resource | ID / ARN | Status | Recorded |
|---|---|---|---|
| VPC `alvs-prod` | `vpc-0f6c992f8a75a6629` (CIDR `10.20.0.0/16`) | shared | B0 discovery |
| Subnet `alvs-prod-pub-1a` (public, us-east-1a) | `subnet-0367b5e29ffc0c525` (`10.20.1.0/24`) | shared | B0 discovery |
| Subnet `alvs-prod-pub-1b` (public, us-east-1b) | `subnet-03e3ec09d37971485` (`10.20.2.0/24`) | shared | B0 discovery |
| Subnet `alvs-prod-iso-1a` (isolated, us-east-1a) | `subnet-0f4865b1984f1ab22` (`10.20.10.0/24`) | shared | B0 discovery |
| Subnet `alvs-prod-iso-1b` (isolated, us-east-1b) | `subnet-0ad36358282f91a16` (`10.20.11.0/24`) | shared | B0 discovery |
| ECS cluster `alvs-prod` | `arn:aws:ecs:us-east-1:789650504128:cluster/alvs-prod` | shared | B0 discovery |
| Shared ALB `alvs-prod-alb` | `arn:aws:elasticloadbalancing:us-east-1:789650504128:loadbalancer/app/alvs-prod-alb/233a09bfb3ba1ce5` (DNS `alvs-prod-alb-18022052.us-east-1.elb.amazonaws.com`, internet-facing) | shared | B0 discovery |
| ALB HTTPS listener (`:443`) | `arn:…:listener/app/alvs-prod-alb/233a09bfb3ba1ce5/6341ecdf783058ba` | shared | B0 discovery |
| ALB HTTP listener (`:80`) | `arn:…:listener/app/alvs-prod-alb/233a09bfb3ba1ce5/68ad7d9016ae1a3f` | shared | B0 discovery |
| Route 53 zone `grupoalvs.com` | `/hostedzone/Z0653783OJDM9CPZYK6Z` (public) | shared | B0 discovery |
| GitHub OIDC provider | `arn:aws:iam::789650504128:oidc-provider/token.actions.githubusercontent.com` | shared | B0 discovery |
| Deploy role `gha-deploy-prod` | `arn:aws:iam::789650504128:role/gha-deploy-prod` | shared | B0 discovery |
| EICE bastion `alvs-prod-eice` | `eice-031506212cc646b43` (subnet `subnet-0367b5e29ffc0c525`, create-complete) | shared | B0 discovery |
| Fargate task SG `alvs-prod-task-sg` | `sg-027b8d1f3fe41007a` | shared | issue #40 (2026-07-12) — confirmed live: pre-existing, also attached to the `sroa-frontend`/`sroa-backend`/`kcbd-backend` services in the `alvs-prod` ECS cluster; matches `TASK_SG_NAME` in `deploy-prod.yml` unchanged, no rename needed. Carried ingress from the ALB SG (`sg-0a03c25d5eac26d26`) on 8000 only; added ingress on 4321 from the same ALB SG for this project's frontend target group — the only mutation made, additive and non-destructive. **2026-07-13 mutation**: added a self-referencing ingress rule, tcp/8000 from `sg-027b8d1f3fe41007a` itself (rule id `sgr-01fbf972cc0bba98b`, description "frontend SSR to backend via Cloud Map") — the frontend task reaches the backend task by the Cloud Map hostname, both share this SG, so the rule must allow the SG to reach itself on 8000 |

### ALB HTTPS rule priorities (state at B0)

Used priorities on the `:443` listener: **9, 10** (`kcbd-api.grupoalvs.com`), **99** (`/ws/*` global), **100, 101** (`sroa.grupoalvs.com`), **109, 110, 111** (`astro-drf-aws.grupoalvs.com`, direct ALB routing — permanent, no CDN, issue #33), plus `default` (404). Rule **109** (host + `/accounts/*` → `tg-astro-drf-aws-backend-prod`) was added 2026-07-12 (issue #37): rule 110's path-pattern condition was already at its 4-value load and could not take a 5th (`/accounts/*`) within the 5-values-per-condition AWS quota, so the auth surface got its own higher-priority rule instead of growing 110.

### Shared attachments this run will add and later remove (never the shared resource itself)

- Repo entry for this repo scoped to `refs/heads/prod` in the `gha-deploy-prod` trust policy (B2.6 → removed in E). **2026-07-19 mutation**: rewritten in place from the name-only form to the immutable subject `repo:kodexArg@47777332/astro-drf-aws@1305504992:ref:refs/heads/prod` — required after the v1 history reset recreated the repo past GitHub's immutable-subject cutoff ([[GH]], [[adr-23-oidc-immutable-subject-claim]], issue #1).
- Statement `BedrockGateNovaMicroInvoke` in the `gha-deploy-prod` inline policy `gha-deploy-prod-policy` (2026-07-19 → removed in E): `bedrock:InvokeModel` on the same four Nova Micro resources as the backend task role's `kdx-router-bedrock-nova-micro` (issue #97), nothing wider. Required by the workflow's `bedrock-live` connectivity gate, which invokes Bedrock as the deploy role before every prod deploy; the grant was missing since the gate landed and no prod push had run green since, so the gap only surfaced on the post-reset deploy (issue #1).
- Host rule + target groups on the shared ALB for `astro-drf-aws.grupoalvs.com` (B2.8 → removed in E).
- Route 53 records under `grupoalvs.com` (B2.7 → removed in E).

## Ephemeral resources

Filled at B2, one row per resource in the same batch as its creation; each carries the Article III tag set. Destroyed and marked `destroyed <date>` in Phase E.

| Resource | ID / ARN | Status | Recorded |
|---|---|---|---|
| Secret `alvs/prod/astro-drf-aws/django` | `arn:aws:secretsmanager:us-east-1:789650504128:secret:alvs/prod/astro-drf-aws/django-3aQ89E` | ephemeral | B2.1 (2026-07-12) |
| Secret `alvs/prod/astro-drf-aws/db` | `arn:aws:secretsmanager:us-east-1:789650504128:secret:alvs/prod/astro-drf-aws/db-57dPTf` | ephemeral | B2.1 (2026-07-12) — `host`/`url` pending RDS (B2.3) |
| Secret `alvs/prod/astro-drf-aws/cognito` | `arn:aws:secretsmanager:us-east-1:789650504128:secret:alvs/prod/astro-drf-aws/cognito-kZbof7` | ephemeral | B2.1 (2026-07-12) — values pending Cognito (B2.2) |
| Secret `alvs/prod/astro-drf-aws/s3` | `arn:aws:secretsmanager:us-east-1:789650504128:secret:alvs/prod/astro-drf-aws/s3-zfIRHq` | ephemeral | B2.1 (2026-07-12) — filled 2026-07-12: issue #33 resolved as a permanent no-CDN decision (adr-02 r5), so `CLOUDFRONT_DOMAIN` is dropped from the secret; `MEDIA_URL` set to Django's local default `/media/` since the S3 storage backend issues presigned URLs directly |
| Secret `alvs/prod/astro-drf-aws/msgraph` | `arn:aws:secretsmanager:us-east-1:789650504128:secret:alvs/prod/astro-drf-aws/msgraph-2vkmEp` | ephemeral | B2.7 (2026-07-13) — `tenant_id`/`client_id`/`client_secret` keys, values sourced from local `.env`; covered by the exec role's existing `alvs/prod/astro-drf-aws/*` wildcard (B2.6) |
| Cognito user pool `alvs-prod-astro-drf-aws` | `us-east-1_IzUPE4fDV` | ephemeral | B2.2 (2026-07-12) — hosted-UI domain `alvs-astro-drf` (prefix fallback, issue #31); confidential client `3t2mknigno1jmtp68si4dj31bi`; test users `test-admin@grupoalvs.com` / `test-user@grupoalvs.com` (creds in the cognito secret only) |
| RDS subnet group `alvs-prod-astro-drf-aws-subnets` | isolated subnets `subnet-0f4865b1984f1ab22`, `subnet-0ad36358282f91a16` | ephemeral | B2.3 (2026-07-12) |
| RDS instance `alvs-prod-astro-drf-aws-pg` | `alvs-prod-astro-drf-aws-pg.cccpxuiv6n1v.us-east-1.rds.amazonaws.com` — PostgreSQL 17.9, `db.t4g.micro`, single-AZ, 20 GB gp3, sg `sg-0c6f4c16f86f7a2b3`, db `app`, no deletion protection, no final snapshot | ephemeral | B2.3 (2026-07-12) |
| S3 bucket `alvs-astro-drf-aws-media-prod` | private, all public access blocked | ephemeral | B2.4 (2026-07-12) |
| ECR `alvs/astro-drf-aws-backend` | `789650504128.dkr.ecr.us-east-1.amazonaws.com/alvs/astro-drf-aws-backend` (immutable tags) | ephemeral | B2.5 (2026-07-12) |
| ECR `alvs/astro-drf-aws-frontend` | `789650504128.dkr.ecr.us-east-1.amazonaws.com/alvs/astro-drf-aws-frontend` (immutable tags) | ephemeral | B2.5 (2026-07-12) |
| IAM roles `alvs-prod-astro-drf-aws-{backend,frontend}-{exec,task}-role` | backend-exec: ECS exec policy + `GetSecretValue` on `alvs/prod/astro-drf-aws/*`; backend-task: media-bucket rw + inline `kdx-router-bedrock-nova-micro` (`bedrock:InvokeModel` on Nova Micro FM ARNs us-east-1/us-east-2/us-west-2 + inference profile `us.amazon.nova-micro-v1:0`, added 2026-07-14, issue #97); frontend roles: exec policy only, **zero secret access** | ephemeral | B2.6 (2026-07-12) — `gha-deploy-prod` trust entry `repo:kodexArg/astro-drf-aws:ref:refs/heads/prod` applied 2026-07-12 (shared-attachment, removed in E) |
| ACM cert `astro-drf-aws.grupoalvs.com` (+SAN `origin-astro-drf-aws.grupoalvs.com`) | `arn:aws:acm:us-east-1:789650504128:certificate/26dc1f46-9e54-4196-9d00-ecaedfd56873` — ISSUED | ephemeral | B2.7 (2026-07-12) — the `origin-astro-drf-aws.grupoalvs.com` SAN is unused as of 2026-07-12 (issue #33 resolved: no CDN, so no origin host is needed); kept as-is, not reissued, since it's the same cert validating the live host name |
| Route 53 record — ACM validation CNAME (host) | `_67bb9ac886bb6b2a2ff29012394bad6b.astro-drf-aws.grupoalvs.com` → `_3796774987649ffc5fb5072e07bf37f0.jkddzztszm.acm-validations.aws` | shared-attachment | B2.7 (2026-07-12) |
| Route 53 record — ACM validation CNAME (origin) + `origin-astro-drf-aws.grupoalvs.com` CNAME → `alvs-prod-alb` | destroyed | destroyed 2026-07-12 | B2.7 (2026-07-12) — removed 2026-07-12: CloudFront permanently out of scope (issue #33), so the origin host and its validation record serve no purpose |
| Route 53 A-alias `astro-drf-aws.grupoalvs.com` → `alvs-prod-alb` | zone `Z0653783OJDM9CPZYK6Z` | shared-attachment | 2026-07-12 — permanent routing per the owner's ruling on issue #33 (adr-02 r5 / adr-12): this template ships without CloudFront; private S3 + Django-issued presigned URLs is the media architecture. No longer "interim" |
| CloudFront OAC `astro-drf-aws-media-oac` | `E38F7J8Z7HXKBG` | destroyed 2026-07-12 | B2.7 (2026-07-12) — created for the media distribution that never shipped; deleted 2026-07-12 when issue #33 resolved CloudFront permanently out of scope |
| Target group `tg-astro-drf-aws-backend-prod` | `arn:…:targetgroup/tg-astro-drf-aws-backend-prod/c6a103483a928fcc` (HTTP 8000, hc `/api/health/`) | ephemeral | B2.8 (2026-07-12) — ALB `:443` rule prio 110 (host + `/api/*` `/admin/*` `/static/*` `/media/*`) added interim (2026-07-12, issue #33 ruling, mirrors `sroa` 100/101); rule prio 109 (host + `/accounts/*`) added 2026-07-12 (issue #37) so the Cognito login/callback surface reaches the backend instead of falling through to the frontend |
| Target group `tg-astro-drf-aws-frontend-prod` | `arn:…:targetgroup/tg-astro-drf-aws-frontend-prod/12fc282614fc74ad` (HTTP 4321, hc `/healthz`) | ephemeral | B2.8 (2026-07-12) — ALB `:443` rule prio 111 (host) added interim (2026-07-12, issue #33 ruling) |
| Cloud Map namespace `astro-drf-aws-prod.local` | private DNS, VPC `alvs-prod` | ephemeral | B2.9 (2026-07-12) |
| Cloud Map service `astro-drf-aws-backend` | `srv-v5isxeycr24bsamg` (namespace `ns-4z5o2ezb7ubihsnp`) | ephemeral | D2 (2026-07-12) — created manually with the ECS services (see below); `gha-deploy-prod` lacks `servicediscovery:*`, so CI never creates it |
| ECS service `astro-drf-aws-backend` | `arn:aws:ecs:us-east-1:789650504128:service/alvs-prod/astro-drf-aws-backend` | ephemeral | D2 (2026-07-12) — created manually on cluster `alvs-prod` per the `sroa`/`kcbd` pattern (services pre-exist, CI is update-only; `gha-deploy-prod` lacks `ecs:CreateService`); tags applied |
| ECS service `astro-drf-aws-frontend` | `arn:aws:ecs:us-east-1:789650504128:service/alvs-prod/astro-drf-aws-frontend` | ephemeral | D2 (2026-07-12) — created manually on cluster `alvs-prod` per the `sroa`/`kcbd` pattern (services pre-exist, CI is update-only); tags applied |
| Log groups `/alvs/astro-drf-aws/{backend,frontend}-prod` | retention 14 days | ephemeral | B2.10 (2026-07-12) |
| VPC interface endpoint `com.amazonaws.us-east-1.bedrock-runtime` | not yet created — see note below | **planned** | issue #95 (2026-07-14) — prepared via `scripts/provision_bedrock_endpoint.sh`; tags on creation: `project=astro-drf-aws`, `env=prod`, `lifecycle=ephemeral` |
| Security group `alvs-prod-bedrock-vpce-sg` | not yet created — see note below | **planned** | issue #95 (2026-07-14) — ingress tcp/443 from `sg-027b8d1f3fe41007a` (`alvs-prod-task-sg`) only |

> [!warning] Not provisioned live — owner action required (issue #95)
> This worker's AWS credentials resolve to account `393022986836` (`arn:aws:iam::393022986836:user/pykodex`), not the reference run's account `789650504128`. Per [[adr-12-ephemeral-run]] rule 2 ("born dead", never faked), the endpoint and its SG are **prepared, not created**. Run `scripts/provision_bedrock_endpoint.sh` with credentials for account `789650504128` (profile `kodex`, per this file's header) to create both resources; then flip these two rows from `planned` to `ephemeral` with the returned `vpce-*`/`sg-*` IDs, in the same batch as creation, per adr-12 rule 5.

> [!note] Permanent no-CDN routing (issue #33, resolved)
> Issue #33 is resolved as a permanent architecture decision, not an interim workaround: this template ships without CloudFront (adr-02 r5 / adr-12). `astro-drf-aws.grupoalvs.com` A-aliases directly to `alvs-prod-alb` (rows above), HTTPS terminated at the ALB with the existing ACM cert, rule prio 110/111 routing to the backend/frontend target groups. Media stays private S3 with Django-issued presigned URLs; the CloudFront OAC created during B2.7 was deleted, and the unused origin host + its Route 53 records were removed. Verified 2026-07-12: DNS resolves, `http` → 301 `https`, `https /` and `/api/health/` → 503 `awselb` (expected — target groups are empty until the ECS services deploy). No reversal is planned.
