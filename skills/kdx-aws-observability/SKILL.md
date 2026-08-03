---
name: kdx-aws-observability
description: >
  Observability for ALVS Fargate Django+Astro: CloudWatch Logs groups, awslogs
  driver, ALB health, minimal metrics/alarms. Use when configuring logging,
  health checks, or baseline monitoring for astro-drf-aws. No ADOT/App Signals
  by default, no X-Ray required, no ElastiCache metrics.
---

# kdx-aws-observability

**Default stack is boring on purpose:** awslogs → CloudWatch Logs + ALB target health. That is enough for `desiredCount: 1` Fargate services. Do not install OpenTelemetry/Application Signals unless the user explicitly asks.

## Fixed log groups

**Canonical (template):**

```
/alvs/<project>/backend-<env>
/alvs/<project>/frontend-<env>
```

Examples live: `/alvs/sroa/backend-prod`, `/alvs/sroa/frontend-dev`, …

**Task definition:**

```json
"logConfiguration": {
  "logDriver": "awslogs",
  "options": {
    "awslogs-group": "/alvs/<project>/<component>-<env>",
    "awslogs-region": "us-east-1",
    "awslogs-stream-prefix": "<env>"
  }
}
```

Create the log group if missing (retention: prefer 14–30 days for cost).

> Note: some legacy task defs may still use `/ecs/alvs-<env>/...`. New work uses `/alvs/...` only.

## What to log (apps)

| Service | Expect |
|---------|--------|
| Backend (Django/DRF) | request id optional; 4xx/5xx; migration errors; gunicorn/uvicorn access+error |
| Frontend (Astro SSR) | SSR errors; upstream Cloud Map fetch failures to backend |

- No secrets in logs (tokens, `SECRET_KEY`, DB password).  
- JSON logs optional; plain text fine at this scale.

## Health checks

| Layer | Path | Notes |
|-------|------|-------|
| ALB TG backend | `/api/health/` per API.md (sroa live may use `/health/` — new projects follow API.md) | HTTP 200 |
| ALB TG frontend | `/` or `/healthz` | document in API if custom |
| Container healthCheck | optional; ALB is source of truth for TG |

## Metrics that matter (keep the set small)

| Metric | Dimension | Alarm? |
|--------|-----------|--------|
| `HealthyHostCount` | TG | yes if 0 for N minutes |
| `UnHealthyHostCount` | TG | yes if > 0 sustained |
| `HTTPCode_Target_5XX_Count` | ALB/TG | yes if burst |
| `CPUUtilization` / `MemoryUtilization` | ECS service | warn only; right-size later |
| RDS `CPUUtilization` / `FreeStorageSpace` | `alvs-<env>-pg` | yes for storage |

No Redis metrics (Redis forbidden). No custom EMF unless needed.

## CLI (profile `kodex`, region `us-east-1`)

```bash
aws logs describe-log-groups --log-group-name-prefix /alvs/<project> --profile kodex --region us-east-1
aws elbv2 describe-target-health --target-group-arn <tg-arn> --profile kodex --region us-east-1
aws ecs describe-services --cluster alvs-<env> --services <project>-backend --profile kodex --region us-east-1
```

## Forbidden defaults

- Requiring X-Ray / ADOT for every service  
- Shipping logs to third-party SaaS without user request  
- Per-request DEBUG logs in prod  
- ElastiCache dashboards  

## Related

`kdx-aws-cloudwatch-query` · `kdx-aws-cloudwatch-alarms` · `kdx-aws-troubleshoot` · `kdx-aws-cost`
