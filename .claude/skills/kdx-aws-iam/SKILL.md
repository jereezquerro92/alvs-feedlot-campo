---
name: kdx-aws-iam
description: >
  ALVS IAM for this template: Fargate exec/task roles, GHA OIDC deploy roles,
  least privilege for Django/Astro on ECS. Use when creating or editing roles,
  trust policies, or task permissions for astro-drf-aws. us-east-1, account
  789650504128. Not for Cognito app RBAC or org-wide IAM redesign.
---

# kdx-aws-iam

**Scope:** IAM roles that touch **astro-drf-aws** on ALVS only. Naming and split match live SROA roles and `docs/INFRASTRUCTURE.md`.

## Fixed context

| Item | Value |
|------|--------|
| Account | `789650504128` |
| Region | us-east-1 |
| Profile | `kodex` (human/agent ops); deploy via **OIDC** roles |
| Envs | dev, prod |

## Role matrix (exactly four app roles per env per project)

| Role name | Principal | Purpose |
|-----------|-----------|---------|
| `alvs-<env>-<project>-backend-exec-role` | `ecs-tasks.amazonaws.com` | Pull ECR, write logs, **read secrets** into container |
| `alvs-<env>-<project>-backend-task-role` | `ecs-tasks.amazonaws.com` | App AWS API (S3 media, etc.) at runtime |
| `alvs-<env>-<project>-frontend-exec-role` | `ecs-tasks.amazonaws.com` | Pull ECR, write logs — **no secrets** |
| `alvs-<env>-<project>-frontend-task-role` | `ecs-tasks.amazonaws.com` | Minimal; usually no AWS API |

Deploy (shared per env, not per project unless required):

| Role | Trust | Purpose |
|------|-------|---------|
| `gha-deploy-<env>` | `token.actions.githubusercontent.com` OIDC | push ECR + `ecs:UpdateService` / register task def |
| `gha-deploy-docs` | same | docs-only pipelines if present |

Live precedent (do not rename): `alvs-prod-sroa-backend-exec-role`, `…-task-role`, same for frontend; `gha-deploy-dev`, `gha-deploy-prod`.

## Trust policies

### ECS roles

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "ecs-tasks.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
```

Prefer condition `aws:SourceAccount` = `789650504128` when creating new roles.

### GHA OIDC

- Provider: `token.actions.githubusercontent.com`  
- Trust scoped to **specific repos** + deploy refs: `refs/heads/main` (dev), `refs/heads/prod` (prod); optional `refs/tags/v*` for releases ([[GH]])
- **Immutable subject format:** repos created/renamed/transferred after GitHub's 2026-07-15 cutoff emit `sub` as `repo:OWNER@OWNER-ID/REPO@REPO-ID:ref:…` — trust entries for them MUST use that form (name-only never matches). Read the live prefix: `gh api repos/OWNER/REPO/actions/oidc/customization/sub`. Format detail: [[GH]], [[adr-23-oidc-immutable-subject-claim]]
- **No long-lived access keys** for CI  

## Permission doctrine

### Exec role (backend)

Must allow:

- `ecr:GetAuthorizationToken` + pull on `alvs/<project>-backend`  
- `logs:CreateLogStream`, `logs:PutLogEvents` on `/alvs/<project>/backend-<env>`  
- `secretsmanager:GetSecretValue` on `alvs/<env>/<project>/*` (and KMS decrypt if a CMK is added later)  

### Task role (backend)

Only what the **Django process** needs:

- S3 object R/W on `alvs-<project>-media-<env>` (and list if required)  
- Nothing for RDS (security groups + password secret, not IAM DB auth unless project opts in)  
- **No** `*` on Secrets Manager from the task role if secrets are injected by the exec role  

### Frontend roles

- Exec: ECR pull + logs only  
- Task: empty or deny-by-default — frontend gets **zero secrets** (`docs/VARIABLES.md`)  

### GHA deploy role

- ECR push to `alvs/<project>-*`  
- `ecs:Describe*`, `RegisterTaskDefinition`, `UpdateService`, `DescribeServices` on cluster `alvs-<env>`  
- Pass role to exec/task roles (`iam:PassRole` scoped to those four ARNs)  

## Forbidden

- AdminAccess / PowerUser on task or exec roles  
- Putting secrets in task env as plain strings to “skip IAM”  
- Shared mega-role across projects  
- IAM users with access keys for deploy  
- Broad `Resource: "*"` on secrets or S3  

## Verify (read-only)

```bash
aws iam get-role --role-name alvs-prod-<project>-backend-exec-role --profile kodex
aws iam list-attached-role-policies --role-name alvs-prod-<project>-backend-exec-role --profile kodex
aws iam list-role-policies --role-name alvs-prod-<project>-backend-exec-role --profile kodex
aws sts get-caller-identity --profile kodex
```

## Related

`kdx-aws-containers` · `kdx-aws-secrets-manager` · `kdx-aws-s3`
