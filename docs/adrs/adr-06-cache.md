---
title: adr-06-cache
type: adr
category: devops
use_case: adding any caching mechanism, writing a response that might skip Cache-Control, caching personalized or authenticated data
created: 2026-07-10
modified: 2026-08-02
tags: [adr, cache]
---

# ADR-06 — cache

## CONTEXT

> Redis never enters the stack. Four layers are the whole cache strategy, and no response leaves without a `Cache-Control` header.

## ASSERTIONS

1. No cache server, ever. Redis and ElastiCache are prohibited; the stack must never grow one.
2. The four layers defined in [[CACHE]] — HTTP, Django shared cache, per-process, Astro — are the whole strategy. No caching mechanism exists outside them.
3. Every response the containers emit carries an explicit `Cache-Control` header; an absent header is a bug, not a default.
4. Authenticated responses are `no-store` by default; caching personalized data is an opt-in, row-level decision in [[API]] — never a blanket policy.

## FORBIDDEN

- **NEVER** add Redis, ElastiCache, or a package requiring either (rule 1). The prohibition is outright, not a preference.
- **NEVER** ship a response with no explicit `Cache-Control` header (rule 3), whatever the framework would default to.
- **NEVER** cache an authenticated response by blanket policy (rule 4). `no-store` is overridden per row in [[API]], never globally.

## RELATED

### related adrs

- [[docs/adrs/adr-50-initial-stack]] — rule 4, the stack-level echo of rule 1

### related files

- [[docs/CACHE]] — the four layers and their mechanics
- [[docs/API]] — where a per-route caching exception is declared
