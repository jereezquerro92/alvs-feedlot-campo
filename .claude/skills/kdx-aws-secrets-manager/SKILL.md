---
name: kdx-aws-secrets-manager
description: >
  Operate and inject AWS Secrets Manager secrets for ALVS Fargate Django/Astro
  tasks. Use when wiring task definition secrets, rotating values, auditing
  secret names, or debugging missing env in containers. Read metadata only by
  default — never dump secret values into chat.
---

# kdx-aws-secrets-manager

Runtime/ops companion to `kdx-aws-secrets-create`. Template SSOT: `docs/VARIABLES.md`.

## Injection model (mandatory)

ECS injects secrets **at task start** via container definition `secrets`:

```json
{
  "name": "DB_PASSWORD",
  "valueFrom": "arn:aws:secretsmanager:us-east-1:789650504128:secret:alvs/prod/<project>/db-XXXXXX:password::"
}
```

- `name` = process env var (must exist in VARIABLES).  
- `valueFrom` = secret ARN **or** partial ARN + **JSON key** (`:key::`).  
- Exec role reads secrets; app code only sees env vars.  
- Frontend task definitions: **secrets array empty always**.

## Inventory (read-only)

```bash
# names only
aws secretsmanager list-secrets --region us-east-1 --profile kodex \
  --query "SecretList[?starts_with(Name, 'alvs/')].Name" --output text

aws secretsmanager describe-secret \
  --secret-id alvs/prod/<project>/db \
  --region us-east-1 --profile kodex
```

**Do not** call `get-secret-value` in agent sessions unless the user explicitly requests a value for a local break-glass task. Prefer describing missing keys by comparing VARIABLES to task def `secrets` names.

## Live naming (ALVS us-east-1)

Observed patterns:

```
alvs/dev/<project>/db|django|s3|...
alvs/prod/<project>/db|django|s3|...
alvs/shared/...          # rare shared secrets — do not put project secrets here
```

Projects already present: `sroa`, `kcbd`. New projects follow the same tree.

## Task definition checklist

| Env var (backend) | Secret | JSON key |
|-------------------|--------|----------|
| `DB_HOST` | `.../db` | `host` |
| `DB_PORT` | `.../db` | `port` |
| `DB_NAME` | `.../db` | `dbname` |
| `DB_USER` | `.../db` | `username` |
| `DB_PASSWORD` | `.../db` | `password` |
| `SECRET_KEY` | `.../django` | `SECRET_KEY` |
| `ALLOWED_HOSTS` | `.../django` | `ALLOWED_HOSTS` |
| `DEBUG` | `.../django` | `DEBUG` |
| `CORS_ALLOWED_ORIGINS` | `.../django` | `CORS_ALLOWED_ORIGINS` |
| `AWS_STORAGE_BUCKET_NAME` | `.../s3` | `AWS_STORAGE_BUCKET_NAME` |
| `AWS_S3_REGION_NAME` | `.../s3` | `AWS_S3_REGION_NAME` |
| `MEDIA_URL` | `.../s3` | `MEDIA_URL` |

Plain (non-secret) backend env: e.g. `USE_X_FORWARDED_PROTO` — **not** in Secrets Manager.

## Failure modes

| Symptom | Likely cause |
|---------|----------------|
| Task stopped `ResourceInitializationError` secrets | Exec role missing `GetSecretValue` or wrong ARN/key |
| App boots with empty `SECRET_KEY` | Secret key name mismatch (case) |
| Frontend somehow has DB password | **Defect** — remove secret from frontend task def |
| Works locally, fails on Fargate | Local `.env` not mirrored in SM / wrong env path `dev` vs `prod` |

## Related

`kdx-aws-secrets-create` · `kdx-aws-iam` · `kdx-aws-containers` · `kdx-aws-troubleshoot`
