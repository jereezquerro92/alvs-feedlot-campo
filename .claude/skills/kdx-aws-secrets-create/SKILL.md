---
name: kdx-aws-secrets-create
description: >
  Create AWS Secrets Manager secrets for astro-drf-aws on ALVS only. Naming
  alvs/<env>/<project>/<component>, JSON blobs matching docs/VARIABLES.md.
  Use when adding db, django, s3, or other component secrets. Never SSM
  Parameter Store. Never put secrets on the frontend task.
---

# kdx-aws-secrets-create

**SSOT for names/keys:** `docs/VARIABLES.md` + `docs/INFRASTRUCTURE.md`.  
**Live account:** ALVS `789650504128`, **us-east-1**. Precedent: `alvs/{dev,prod}/sroa/{db,django,s3}`, `alvs/{dev,prod}/kcbd/...`.

## Rules

1. **Secrets Manager only** — never SSM Parameter Store, never committed `.env` in git, never plaintext task `environment` for secret values.  
2. **Name:** `alvs/<env>/<project>/<component>`  
   - env ∈ `dev` | `prod`  
   - component ∈ `db` | `django` | `s3` | project-specific (`cognito`, `ingest`, …) registered in VARIABLES first  
3. **Value:** single JSON object. Task definition maps **each key** via `valueFrom` JSON key.  
4. **Frontend:** create **no** secrets for frontend tasks.  
5. **Local:** developers mirror names in gitignored `.env`; cloud always Secrets Manager.  
6. Do **not** invent automatic rotation Lambdas unless the user explicitly asks (ALVS live secrets use default encryption; KmsKeyId often null).  
7. Tag secrets: `App=<project>`, `Role=<component>-secret`, optional `Env=<env>`.

## Standard secret bodies

Keys must match `docs/VARIABLES.md`. Do not add undeclared keys.

### `alvs/<env>/<project>/db`

```json
{
  "host": "<rds-endpoint>",
  "port": "5432",
  "dbname": "<db>",
  "username": "<user>",
  "password": "<password>",
  "url": "postgresql://..."
}
```

RDS instances (read-only survey): `alvs-dev-pg`, `alvs-prod-pg` — **PostgreSQL 17.9**, `db.t4g.micro`, not public, isolated subnets.

### `alvs/<env>/<project>/django`

```json
{
  "SECRET_KEY": "...",
  "ALLOWED_HOSTS": "<project>.grupoalvs.com,...",
  "DEBUG": "false",
  "CORS_ALLOWED_ORIGINS": "https://..."
}
```

Prod: `DEBUG` never true.

### `alvs/<env>/<project>/s3`

```json
{
  "AWS_STORAGE_BUCKET_NAME": "alvs-<project>-media-<env>",
  "AWS_S3_REGION_NAME": "us-east-1",
  "MEDIA_URL": "/media/"
}
```

No CDN domain here — the bucket is private and django-storages issues presigned URLs directly per object ([[CACHE]], `kdx-aws-s3`).

## Create procedure (CLI)

```bash
# After VARIABLES row exists and values are approved by the human
aws secretsmanager create-secret \
  --name "alvs/<env>/<project>/<component>" \
  --description "<project> <component> <env>" \
  --secret-string 'file://secret.json' \
  --tags Key=App,Value=<project> Key=Role,Value=<component>-secret \
  --region us-east-1 --profile kodex
```

Update (new version, no name change):

```bash
aws secretsmanager put-secret-value \
  --secret-id "alvs/<env>/<project>/<component>" \
  --secret-string 'file://secret.json' \
  --region us-east-1 --profile kodex
```

**Never print secret values into chat logs or commit them.** Prefer `file://` over inline strings when values are sensitive.

## After create

1. Wire task definition `secrets` (exec role needs `GetSecretValue`) → `kdx-aws-containers` + `kdx-aws-iam`.  
2. Redeploy service.  
3. Confirm app boot without KeyError on settings.

## Forbidden

- One mega-secret for the whole account  
- Storing GHA OIDC tokens as app secrets  
- Duplicating the same password in django + db secrets under different shapes without VARIABLES rows  
- Creating secrets “for later” without VARIABLES  

## Related

`kdx-aws-secrets-manager` · `kdx-aws-iam` · `kdx-aws-containers` · `kdx-django-6-drf`
