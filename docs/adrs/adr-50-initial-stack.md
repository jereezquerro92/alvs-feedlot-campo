---
title: adr-50-initial-stack
type: adr
category: devops
use_case: adding a package, tool or runtime, re-pinning a version, or reaching for infrastructure the project does not already run
created: 2026-07-10
modified: 2026-08-07
tags: [adr, stack, infrastructure, requirements]
---

# ADR-02 — the initial allowed stack

## CONTEXT

> The stack is a closed list, and [[REQUIREMENTS]] is the list. Anything absent from it is not in the stack yet — adding it means adding its row first.

## ASSERTIONS

1. The allowed stack is exactly what [[REQUIREMENTS]] pins. A package, tool, or runtime absent from that file is not in the stack; adding one means adding its row — version, status, check date — first.
2. Version policy is owned by [[REQUIREMENTS]]: latest available, beta acceptable. Every re-pin re-runs that policy and records its check date there.
3. Toolchains: `uv` for everything Python ([[BACKEND]]); `bun` — package manager AND runtime — for everything JavaScript ([[FRONTEND]]).
4. The cache strategy is the four layers [[CACHE]] defines, ruled by [[adr-06-cache]]. The sanctioned cloud shared-cache server is ElastiCache Valkey as that ADR and [[CACHE]] state; connection packages enter [[REQUIREMENTS]] with the Valkey wiring, never as a second cache product.
5. The infrastructure is the two-Fargate AWS layout owned by [[INFRASTRUCTURE]] — clusters, networking, ALB routing, ECR, service discovery, logs, IAM, CI/CD all follow that file.
6. Secrets live in AWS Secrets Manager only; the variable inventory is [[VARIABLES]]. Database rules are owned by [[BD]].

## FORBIDDEN

- **NEVER** install with npm, pnpm or yarn (rule 3). `bun` is both package manager and runtime; a second lockfile is a second answer to what version is installed.
- **NEVER** run Node as a runtime (rule 3). It stays a documented fallback and nothing else.
- **NEVER** add unmanaged Redis or a non-Valkey cache server (rule 4). The Valkey pick and the four layers belong to [[adr-06-cache]] and [[CACHE]]; a second product beside that pick is a stack divergence.
- **NEVER** diverge from [[INFRASTRUCTURE]] by local exception (rule 5). A divergence is a new ADR, never a shape quietly run beside the documented one.

## REJECTED

- **No cache server in the stack** — rule 4 until 2026-08-07 forbade Redis and ElastiCache outright and kept layer 2 on `DatabaseCache` only. Replaced by the owner pick of ElastiCache Valkey (`cache.t4g.micro`, single-node, no Multi-AZ until traffic justifies more) under [[adr-06-cache]] rule 1. It would reopen only if that pick were withdrawn.

## RELATED

### related adrs

- [[docs/adrs/adr-06-cache]] — owns the Valkey pick this ADR echoes

### related files

- [[docs/constitution/REQUIREMENTS]] — the pinned list; the stack is whatever it says
- [[docs/constitution/INFRASTRUCTURE]] — the AWS layout rule 5 defers to
- [[docs/VARIABLES]] — the variable inventory
- [[docs/BD]] — database rules
- [[docs/BACKEND]] / [[docs/FRONTEND]] — where each toolchain is applied
- [[docs/CACHE]] — Valkey sizing and the four layers
