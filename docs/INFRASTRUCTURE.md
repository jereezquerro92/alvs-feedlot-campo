---
title: INFRASTRUCTURE
type: reference
status: active
created: 2026-07-10
tags: [harness, infrastructure, aws]
---

# INFRASTRUCTURE

AWS layout for the Astro SSR + DRF pair: **two Fargate services** per project, region **us-east-1**, ALVS account. Conventions mirror the SROA production precedent (surveyed 2026-07-10). `<project>` is the placeholder for the project slug — carried at runtime by `PROJECT_SLUG` / `BASE_DOMAIN` ([[VARIABLES]]). This template's own reference project is **`astro-drf-aws`** → hosts `astro-drf-aws.dev.grupoalvs.com` / `astro-drf-aws.grupoalvs.com` ([[GLOSSARY]]).

> [!note]
> Environments are **dev and prod only** — no staging tier exists in this account.

Database specifics → [[BD]]. Variable and secret contents → [[VARIABLES]]. Cache behavior → [[CACHE]]. Version pins → [[REQUIREMENTS]].

## ECS

- One cluster per env: `alvs-dev`, `alvs-prod`.
- Two services per project: `<project>-backend`, `<project>-frontend`.
- Launch type Fargate, network mode `awsvpc`.
- Baseline sizing: **256 CPU / 512 MB**, `desiredCount: 1`. Scale up only when measured.

## Networking

- One VPC per env: dev `10.10.0.0/16`, prod `10.20.0.0/16`. Two AZs each.
- **Public subnets**: ALB + Fargate tasks (tasks get public IPs).
- **Isolated subnets**: RDS only ([[BD]]).

> [!warning]
> **No NAT gateways — deliberate cost trade-off.** Tasks reach the internet through their public IPs. This diverges from the textbook private-subnet layout on purpose. Do not "fix" it by adding NAT.

### Accepted risk: public task IPs

Consequent to the no-NAT trade-off above, every Fargate task — the backend and frontend services **and** the one-off migrate task — is launched with `assignPublicIp=ENABLED` into the public subnets (`deploy-prod.yml`: `PUBLIC_SUBNET_A`/`PUBLIC_SUBNET_B`, the `awsvpcConfiguration` built for the migrate task run and reused for the service network configs). This is a **deliberate, accepted cost trade-off**, not an oversight — do not read it as a security bug or "fix" it unilaterally.

> [!warning] Accepted risk, not a finding
> Task ENIs are internet-routable, and the task security group (`alvs-<env>-task-sg`) is the sole isolation layer — no NAT, no private subnet, no network ACL beyond the SG. The migrate task in particular carries `DB_PASSWORD` and `SECRET_KEY` as env secrets while holding a public IP. The trade-off is accepted for cost reasons consistent with the "No NAT gateways" decision immediately above; it is not silently accepted risk, it is documented accepted risk.

**Contrast and optional future path.** Isolated subnets already exist for this project, RDS-only today (`alvs-prod-iso-1a` / `alvs-prod-iso-1b`, [[INVENTORY]]). A future hardening — moving Fargate tasks into isolated subnets with `assignPublicIp=DISABLED`, plus VPC interface endpoints for ECR, Secrets Manager, and CloudWatch Logs (mirroring the Bedrock endpoint pattern below) — is named here as optional future work. It is not silently precluded, but it is out of scope for this note and requires its own issue and engagement with this file's ownership ([[adr-02-initial-stack]] rule 5) before it is pursued.

### Bedrock VPC interface endpoint

- **`com.amazonaws.us-east-1.bedrock-runtime`** interface endpoint, one per env, placed in that env's **public subnets** (the same subnets the Fargate tasks run in — this stack has no isolated/private application subnet; RDS's isolated subnets are DB-only and out of scope here).
- **Private DNS enabled** — the backend resolves `bedrock-runtime.us-east-1.amazonaws.com` to the endpoint's private ENIs with zero code change ([[BACKEND]], async wrap per [[adr-16-async-mandatory]] rule 4).
- Security group `alvs-<env>-bedrock-vpce-sg` — ingress tcp/443 from `alvs-<env>-task-sg` only; interface endpoints originate no outbound connections, so no egress rule is required.
- Purpose: lets the backend reach Bedrock without a NAT gateway, keeping the no-NAT trade-off above and [[adr-02-initial-stack]] rule 5 intact — this is the private-networking path Bedrock inference needs instead of public-IP egress.

## Containers

| Component | Port | Runtime | Repo path |
|---|---|---|---|
| backend | 8000 | ASGI ([[BACKEND]]) | `backend/` |
| frontend | 4321 | Astro SSR, host `0.0.0.0` ([[FRONTEND]]) | `frontend/` |

Local images and Compose: [[DOCKER]] (root `compose.yaml` only; Dockerfiles under each path).

## ECR

- Repos: `alvs/<project>-backend`, `alvs/<project>-frontend`.
- Image tags: `<env>-<full-git-sha>`. No `latest`, no mutable tags.

## ALB

- One **shared** internet-facing ALB per env: `alvs-<env>-alb`. Every project on the env rides the same ALB via host rules.
- `:80` → redirect to `:443`. TLS 1.3 policy on `:443`.
- Default action: **404** for unknown hosts.
- One host per project: `<project>.dev.grupoalvs.com` (dev) / `<project>.grupoalvs.com` (prod).
- Path rules, by priority, route to the **backend** target group:
  1. `/accounts/*`
  2. `/ws/*`
  3. `/api/*`
  4. `/admin/*`
  5. `/static/*`
  6. `/media/*`
- Catch-all for the host → **frontend** target group.
- Target groups: `tg-<project>-<component>-<env>`.

## Service discovery

- Cloud Map private DNS namespace per project per env: `<project>-<env>.local`.
- Frontend SSR calls hit the backend at `backend.<project>-<env>.local:8000` — the service segment is the bare `CLOUDMAP_SERVICE` value (`backend`), not `<project>-backend`.
- In prod, the task security group has a self-referencing ingress rule on tcp/8000 (rule ID `sgr-01fbf972cc0bba98b`) to permit frontend → backend traffic via Cloud Map.

> [!important]
> SSR-to-backend traffic goes through Cloud Map only — **never via the public ALB**.

The backend's `ALLOWED_HOSTS` ([[VARIABLES]]) **must include the Cloud Map hostname** (`backend.<project>-<env>.local`) **in addition to the public domain**, or Django rejects the SSR fetch as `DisallowedHost`. Example prod value: `backend.astro-drf-aws-prod.local,astro-drf-aws.grupoalvs.com`.

## Secrets

- **AWS Secrets Manager only.** No SSM Parameter Store.
- Naming: `alvs/<env>/<project>/<component>` (components: `db`, `django`, `s3`, `cognito`, …). Each secret is a JSON blob; task definitions pull individual keys.
- Frontend tasks receive plain `PUBLIC_*` env only — **zero secrets**.
- The variables themselves are declared in [[VARIABLES]] — the SSOT.

> [!warning] The live Cognito pool is the shared org pool, not the look-alike project pool
> `alvs-auth.auth.us-east-1.amazoncognito.com` and app client `72osii98jin6l92ji0gcvv22ec` are actually served by **`us-east-1_YrRbIScNL`** (`alvs-org-pool`), a **shared org-wide pool**. The similarly-named `us-east-1_IzUPE4fDV` (`alvs-prod-astro-drf-aws`) has **zero identity providers configured** and is not in use. Inspect `alvs-org-pool` when debugging auth for this project, not the project-named pool.

## Logs and IAM

- CloudWatch log groups: `/alvs/<project>/<component>-<env>`, stream prefix = env.
- IAM roles: `alvs-<env>-<project>-<component>-{exec,task}-role`.

### Bedrock inference grant (router)

The backend **task** role carries an inline policy (`kdx-router-bedrock-nova-micro`) granting `bedrock:InvokeModel` — scoped to the model, never `bedrock:*`. Nova models are invoked through their **cross-region inference profile** (`us.amazon.nova-micro-v1:0` — the `ROUTER_BEDROCK_MODEL_ID` value, [[VARIABLES]]), so the grant names the profile **and** its underlying foundation models in each region it can route to:

```json
"Action": "bedrock:InvokeModel",
"Resource": [
  "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-micro-v1:0",
  "arn:aws:bedrock:us-east-1:<account>:inference-profile/us.amazon.nova-micro-v1:0",
  "arn:aws:bedrock:us-east-2::foundation-model/amazon.nova-micro-v1:0",
  "arn:aws:bedrock:us-west-2::foundation-model/amazon.nova-micro-v1:0"
]
```

> [!important] Deploy prerequisite — model access is NOT IAM
> Bedrock additionally requires **per-account/region model access** to be enabled (Bedrock console → Model access, or `aws bedrock get-foundation-model-availability --model-id amazon.nova-micro-v1:0` must report `AUTHORIZED`/`AVAILABLE`). This toggle is entirely separate from IAM policy. Both gaps fail with an identical-looking `AccessDeniedException` — the triage recipe lives in [[CHATBOT]].

## DNS

- **No CDN in this template.** User-facing host `<project>[.dev].grupoalvs.com` A-aliases directly to the shared ALB — deliberate: these are internal, authenticated apps whose content is not edge-cacheable.
- Media: private S3 bucket `alvs-<project>-media-<env>`, never public; Django issues short-lived presigned URLs per object ([[BACKEND]], `kdx-aws-s3`).
- Statics: served directly by the backend container behind the ALB `/static/*` rule ([[BACKEND]]) — Django statics are admin + DRF browsable API only, low enough volume that no S3/edge tier is needed.
- Cache behavior rules live in [[CACHE]].

## CI/CD

- GitHub Actions with **OIDC** (`token.actions.githubusercontent.com`) — no long-lived AWS keys.
- Per-env deploy roles: `gha-deploy-<env>`; trust policy scoped to specific repos. `sub` entries for repos created/renamed/transferred after GitHub's immutable-subject cutoff use the immutable format with owner/repo numeric IDs — format, cutoff, and this repo's live values in [[GH]] ([[adr-23-oidc-immutable-subject-claim]]).
- **Branch → env:** `refs/heads/main` → **dev** deploy; `refs/heads/prod` → **prod** deploy. Release tags `v*` may also trigger prod when defined in workflow. Git rules: [[GH]], [[adr-08-github-and-git]]. For the template's own run the `dev ← main` leg is out of scope — see "Ephemeral reference run" below ([[adr-12-ephemeral-run]]).
- Direct push to `main`/`prod` is `kodexArg` only; CI still runs on those refs after their land.
- Pipeline: build image → push to ECR → update ECS service.

## Security groups

Chain, strictly one-directional:

1. `alvs-<env>-alb-sg` — public 80/443.
2. `alvs-<env>-task-sg` — ingress from the ALB SG only. When frontend and backend tasks share one task SG (as in the reference run, [[INVENTORY]]), the SSR-to-backend Cloud Map call ([[Service discovery]] above) additionally needs a self-referencing ingress rule (task SG → itself, tcp/8000) — the ALB-only rule alone does not cover task-to-task traffic.
3. `alvs-<env>-rds-sg` — 5432 from the task SG only.

DB admin access goes through an **EC2 Instance Connect Endpoint bastion** — see [[BD]].

## Ephemeral reference run

Governs the template's own reference deploy (project `astro-drf-aws`), ruled by [[adr-12-ephemeral-run]]. General multi-project doctrine above is unchanged; this section only narrows it for this run.

- **Cloud scope: prod only.** No dev cloud environment is provisioned for this run; the `dev ← main` pipeline above remains doctrine for real projects but is not exercised here. `prod` is the only branch reaching AWS, and OIDC deploy trust is scoped to `refs/heads/prod` only.
- **Mandatory tag set** — every resource created for this run carries all three tags:

  | Tag key | Value | Purpose |
  |---|---|---|
  | `project` | `astro-drf-aws` | scoping / cost attribution |
  | `env` | `prod` | environment |
  | `lifecycle` | `ephemeral` | teardown selector |

- **Inventory:** `docs/INVENTORY.md` is the committed record — columns: name, ARN, `shared` \| `ephemeral`, creating step. It is updated **in the same batch** as each resource's creation. Teardown executes from it and verifies against the Resource Groups Tagging API.
- **Shared pre-existing ALVS resources are never destroyed** — VPC, ECS cluster, shared ALB, Route 53 zone, the GitHub OIDC provider, `gha-deploy-prod`, the EICE bastion. Only this project's attachments are removed (host rule, target groups, DNS records, the trust-policy repo entry).
- **Teardown order** (`lifecycle=ephemeral` rows only): ECS services → ALB host rule + target groups → Cloud Map namespace → Route 53 records + ACM cert → ECR repos → log groups + alarms → IAM roles + this repo's `gha-deploy-prod` trust entry → Cognito hosted-UI domain + user pool → RDS (skip final snapshot, backups removed) → S3 buckets → **secrets last**, `delete-secret --force-delete-without-recovery`. Verified empty when the Tagging API query `project=astro-drf-aws ∧ lifecycle=ephemeral` returns the empty set.
