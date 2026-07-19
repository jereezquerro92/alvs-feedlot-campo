---
name: kdx-aws-troubleshoot
description: >
  Diagnose failing ALVS Fargate Django/Astro deploys: task stops, unhealthy
  targets, secret injection, Cloud Map SSR calls, RDS connectivity. Use when
  a service is down or deploy fails. Read-only first; us-east-1 profile kodex.
---

# kdx-aws-troubleshoot

## Order of operations (always)

1. **Identity** — `aws sts get-caller-identity --profile kodex` (account must be `789650504128`).  
2. **Service** — running vs desired on `alvs-<env>`.  
3. **Events** — ECS service events (last failure reason).  
4. **Task** — stopped reason / essential container exit.  
5. **TG health** — ALB target health + reason.  
6. **Logs** — `kdx-aws-cloudwatch-query` on `/alvs/<project>/...`.  
7. **Config** — task def image tag, secrets, env, SG, subnets.

Do **not** jump to rewriting IAM or recreating clusters.

## Command pack

```bash
export AWS_PROFILE=kodex AWS_DEFAULT_REGION=us-east-1
CLUSTER=alvs-prod   # or alvs-dev
SVC=<project>-backend

aws ecs describe-services --cluster $CLUSTER --services $SVC \
  --query 'services[0].{status:status,desired:desiredCount,running:runningCount,events:events[:5],td:taskDefinition}'

aws ecs list-tasks --cluster $CLUSTER --service-name $SVC --desired-status STOPPED
aws ecs describe-tasks --cluster $CLUSTER --tasks <taskArn> \
  --query 'tasks[0].{stop:stoppedReason,containers:containers[*].{n:name,reason:reason,exit:exitCode}}'

aws elbv2 describe-target-health --target-group-arn <tg-arn>
```

## Failure map

| Symptom | Check |
|---------|--------|
| `CannotPullContainerError` | ECR repo/tag; exec role ECR perms; image never pushed |
| `ResourceInitializationError` + secrets | secret name/key; exec role `GetSecretValue` (`kdx-aws-secrets-manager`) |
| Task running, TG unhealthy | health path/port; security group ALB→task; app not listening 0.0.0.0 |
| Backend 5xx after deploy | logs Traceback; migrations not run; bad `DEBUG`/hosts |
| Frontend OK, API fail from browser | ALB path rules `/api/*` → backend TG; host header |
| Frontend SSR cannot call API | Cloud Map name `BACKEND_API_URL`; task SG; backend listening 8000 |
| DB connection errors | RDS SG allows task SG; secret host; `alvs-<env>-pg` status |
| OOM / exit 137 | Fargate memory too low; raise using valid pair (`kdx-aws-containers`) |

## Network expectations (do not “fix”)

- Tasks in **public** subnets with **public IP** — no NAT.  
- RDS in **isolated** subnets; only `alvs-<env>-task-sg` → 5432 on `alvs-<env>-rds-sg`.  
- SSR → backend via **Cloud Map**, not public ALB.

## Health paths

- Prefer template `GET /api/health/` for backend (declare in API.md).  
- Live sroa TGs may show `/health/` — when debugging sroa, use the live path; when building new projects, use API.md.

## Related

`kdx-aws-containers` · `kdx-aws-cloudwatch-query` · `kdx-aws-secrets-manager` · `kdx-aws-iam`
