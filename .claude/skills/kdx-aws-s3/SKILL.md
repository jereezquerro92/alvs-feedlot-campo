---
name: kdx-aws-s3
description: >
  Media S3 buckets for astro-drf-aws on ALVS: alvs-<project>-media-<env>,
  private, no CDN — Django issues presigned URLs directly via `STORAGES`.
  Use when creating or hardening media buckets. Not for general data lakes
  or public website hosting.
---

# kdx-aws-s3

## Fixed pattern

| Item | Value |
|------|--------|
| Bucket | `alvs-<project>-media-<env>` |
| Region | us-east-1 |
| Live example | `alvs-astro-drf-aws-media-prod` |
| Access | **private** bucket, all public access blocked; no CloudFront, no OAC — this template ships without a CDN ([[INFRASTRUCTURE]], [[CACHE]]) |
| App | Django 6 `STORAGES` (not legacy `DEFAULT_FILE_STORAGE`) via secrets in `alvs/<env>/<project>/s3` |

Static assets for the Astro app are **not** this bucket's job — this skill is **user media** only. Django statics (admin + DRF browsable API) are served directly by the backend container behind the ALB `/static/*` rule, no S3 involved ([[BACKEND]]).

## Create / harden checklist

1. Create bucket in **us-east-1**, name exact.
2. **Block Public Access** = all four ON.
3. Default encryption SSE-S3 (or SSE-KMS if account standard requires).
4. Versioning optional (prefer on for prod media).
5. Bucket policy: **no public statement, no CDN principal.** Access is exclusively through the backend task role's IAM permissions and the presigned URLs Django's storage backend issues per object.
6. Backend **task role** may `s3:PutObject` / `GetObject` / `DeleteObject` on `arn:aws:s3:::alvs-<project>-media-<env>/*` (and `ListBucket` if needed).
7. CORS only if browser uploads go direct to S3 (prefer app-mediated upload unless specified).

## Django wiring — private bucket, presigned URLs, no edge

The bucket stays private; every `FileField.url` call returns an S3-signed URL with a short expiry, generated server-side by django-storages' `S3Boto3Storage` (default `querystring_auth=True`, `AWS_QUERYSTRING_EXPIRE` tunable). No distribution, no OAC, no origin alias — the URL goes straight from Django to the browser to S3.

Secrets JSON (`kdx-aws-secrets-create`):

- `AWS_STORAGE_BUCKET_NAME`
- `AWS_S3_REGION_NAME` = `us-east-1`
- `MEDIA_URL` — Django's local default (`/media/`); vestigial once the storage backend issues presigned URLs directly, kept for local-disk dev storage.

Use modern `STORAGES["default"]` backend for S3. Never commit keys — task role credentials on Fargate.

## Forbidden

- Public-read ACL buckets, bucket policies, or any principal that grants anonymous/edge `s3:GetObject`
- Reintroducing CloudFront or an OAC for this bucket — out of scope for this template ([[INFRASTRUCTURE]])
- Using media bucket as Terraform state or log dump
- Cross-region replication by default
- Redis or local disk as "prod media"

## Verify (read-only)

```bash
aws s3api get-bucket-location --bucket alvs-<project>-media-prod --profile kodex
aws s3api get-public-access-block --bucket alvs-<project>-media-prod --profile kodex
aws s3api get-bucket-policy --bucket alvs-<project>-media-prod --profile kodex   # expect NoSuchBucketPolicy
```

## Related

`kdx-aws-iam` · `kdx-aws-secrets-create` · `kdx-django-6-drf`
