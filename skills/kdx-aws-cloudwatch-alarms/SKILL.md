---
name: kdx-aws-cloudwatch-alarms
description: >
  Minimal CloudWatch alarms for ALVS Fargate astro-drf-aws services: target
  health, 5xx, RDS storage. Use when adding or reviewing alarms/SNS for a
  project. Keep the set tiny; no elasticache, no Lambda noise.
---

# kdx-aws-cloudwatch-alarms

## Philosophy

`desiredCount: 1` + cost discipline → **few alarms**, high signal. Prefer SNS email to on-call for prod only.

## Alarm set (per project, per env)

| # | Name pattern | Metric | Threshold idea |
|---|--------------|--------|----------------|
| 1 | `alvs-<env>-<project>-backend-unhealthy` | TG `UnHealthyHostCount` | ≥ 1 for 2–3 periods |
| 2 | `alvs-<env>-<project>-frontend-unhealthy` | same on frontend TG | same |
| 3 | `alvs-<env>-<project>-backend-5xx` | ALB/TG `HTTPCode_Target_5XX_Count` | > N in 5 min |
| 4 | `alvs-<env>-pg-storage` (shared DB) | RDS `FreeStorageSpace` | low water mark |

Optional later: ECS CPU > 80% for 15m (right-size signal, not page).

## Naming / tags

- Alarm name prefix `alvs-<env>-`  
- Tag `App=<project>`, `Env=<env>`  
- Actions: SNS topic `alvs-<env>-alerts` (create once per env if missing)

## SNS

```bash
aws sns create-topic --name alvs-prod-alerts --region us-east-1 --profile kodex
# subscribe email — human must confirm
```

Link alarms with `AlarmActions` = topic ARN. Encrypt topic if account policy requires it.

## Do not create

- Alarms for Redis/ElastiCache  
- Dozens of per-URL synthetic canaries by default  
- Billing alarms here → `kdx-aws-cost`  
- Alarms that fire on every deploy blip (use longer evaluation periods)

## Verify

```bash
aws cloudwatch describe-alarms --alarm-name-prefix alvs- --profile kodex --region us-east-1
aws elbv2 describe-target-groups --query "TargetGroups[?contains(TargetGroupName, '<project>')].[TargetGroupName,TargetGroupArn]" --profile kodex --region us-east-1
```

## Related

`kdx-aws-observability` · `kdx-aws-troubleshoot` · `kdx-aws-cost`
