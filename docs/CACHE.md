---
title: CACHE
type: reference
status: active
created: 2026-07-10
tags: [harness, cache]
---

# CACHE

The enforced cache strategy for both services. Backend integration rules in [[BACKEND]]; frontend rules in [[FRONTEND]]; the ALB topology is owned by [[INFRASTRUCTURE]].

No cache server, ever ([[adr-06-cache]]): **Redis and ElastiCache are prohibited in this template.** The stack must never grow a cache server. The four layers below are sufficient by design — the trade is deliberate: lower cost and operational simplicity on Fargate over microsecond cache hits.

## Layer 1 — HTTP (first line)

- No CDN sits in front of the ALB in this template ([[INFRASTRUCTURE]]) — the app is internal/authenticated and its content is not edge-cacheable. `Cache-Control` headers are still the **primary** cache mechanism for Astro SSR responses and any cacheable API responses, honored by the browser and any intermediate proxy. Why: a header the client honors scales for free; a server-side cache does not.
- Media is private in S3, served through short-lived presigned URLs Django issues per object — never public, never cached at an edge ([[INFRASTRUCTURE]]).
- Static assets (admin + DRF browsable API only, [[BACKEND]]) are served directly by the backend container behind the ALB `/static/*` rule — they still carry an explicit `Cache-Control`, they just don't hit a CDN.
- Every response the containers emit MUST carry an explicit `Cache-Control`; an absent header is a bug, not a default.

## Layer 2 — Django shared cache

- `DatabaseCache` is the **default** cache backend. It is shared across all Fargate tasks with zero extra infrastructure — the property Redis would otherwise provide.
- The cache table is created with `createcachetable` (part of deploy/setup, not improvised).
- Define sane TTLs per use — short by default — and explicit `MAX_ENTRIES`/`CULL_FREQUENCY` so the table cannot grow unbounded. Cache keys follow [[GLOSSARY]] naming.

## Layer 3 — per-process (narrow use)

- `LocMemCache` exists as a **secondary alias** for hot, staleness-tolerant lookups only (e.g. site flags read on every request).
- Limitation, stated plainly: **each Fargate task has its own copy** — no invalidation propagates between tasks. Never put anything here whose staleness across tasks would be user-visible as inconsistency.
- Example: `apps/m365/graph.py` caches resolved workbook cell values in a module-level dict keyed by cell address, 60s TTL — staleness-tolerant, read-heavy, no cross-task consistency requirement.

## Layer 4 — Astro

- Prefer **prerendering / static output** for pages that do not need SSR; a page that can be static never spends a container cycle.
- SSR responses set explicit `Cache-Control` per route ([[FRONTEND]]).

Default-deny for authenticated responses ([[adr-06-cache]]): authenticated API responses are `no-store` unless a row-level decision in [[API]] says otherwise. Caching personalized data is opt-in per endpoint, never a blanket policy.
