---
title: adr-02-initial-stack
type: adr
status: active
created: 2026-07-10
tags: [adr, stack, infrastructure, requirements]
---

# ADR-02 — the initial allowed stack

Rules only; content lives in [[REQUIREMENTS]] and [[INFRASTRUCTURE]].

1. The allowed stack is exactly what [[REQUIREMENTS]] pins. A package, tool, or runtime absent from that file is not in the stack; adding one means adding its row — version, status, check date — first.
2. Version policy is owned by [[REQUIREMENTS]]: latest available, beta acceptable. Every re-pin re-runs that policy and records its check date there.
3. Toolchains: `uv` for everything Python ([[BACKEND]]); `bun` — package manager AND runtime — for everything JavaScript ([[FRONTEND]]). npm is prohibited; Node is not in the stack (documented fallback only).
4. Redis and any cache server are prohibited ([[CACHE]], ruled by [[adr-06-cache]]).
5. The infrastructure is the two-Fargate AWS layout owned by [[INFRASTRUCTURE]] — clusters, networking, ALB routing, ECR, service discovery, logs, IAM, CI/CD all follow that file. Diverging from it requires a new ADR, never a local exception.
6. Secrets live in AWS Secrets Manager only; the variable inventory is [[VARIABLES]]. Database rules are owned by [[BD]].
