---
title: CACHE
type: reference
category: backend
use_case: caching a response, or reaching for a cache server
created: 2026-07-10
modified: 2026-08-07
tags: [doc, harness, cache]
---

# CACHE

The enforced cache strategy for both services. Backend integration rules in [[BACKEND]]; frontend rules in [[FRONTEND]]; the ALB topology and ElastiCache placement are owned by [[INFRASTRUCTURE]].

Why four layers plus one small Valkey node ([[adr-06-cache]]): HTTP headers stay free; a single-node `cache.t4g.micro` Valkey gives shared in-memory state across Fargate tasks without Multi-AZ cost until traffic proves the need.

## Recorded decision (2026-08-07) — ElastiCache Valkey

Owner pick for the cloud shared Django cache:

| Setting | Value |
|---|---|
| Engine | **Valkey** (ElastiCache) |
| Node class | **`cache.t4g.micro`** |
| Topology | **single-node**, **no Multi-AZ** |
| Resize trigger | measured traffic / eviction / CPU — not anticipation |

Local layer 2 stays **`DatabaseCache`** (Compose does not run Valkey — [[DOCKER]], [[adr-09-docker-compose]] rule 6). Wiring Django to Valkey in cloud, the connection env names in [[VARIABLES]], and the REQUIREMENTS pin are implementation follow-ons authorized by this decision and [[adr-06-cache]] rule 1.

## Layer 1 — HTTP (first line)

- No CDN sits in front of the ALB in this template ([[INFRASTRUCTURE]]) — the app is internal/authenticated and its content is not edge-cacheable. `Cache-Control` headers are still the **primary** cache mechanism for Astro SSR responses and any cacheable API responses, honored by the browser and any intermediate proxy. Why: a header the client honors scales for free; a server-side cache does not.
- Media is private in S3, served through short-lived presigned URLs Django issues per object — never public, never cached at an edge ([[INFRASTRUCTURE]]).
- Static assets (admin + DRF browsable API only, [[BACKEND]]) are served directly by the backend container behind the ALB `/static/*` rule — they still carry an explicit `Cache-Control`, they just don't hit a CDN.

## Layer 2 — Django shared cache

- **Cloud:** ElastiCache Valkey (pick above) is the shared cache backend across Fargate tasks.
- **Local:** `DatabaseCache` remains the shared backend — zero extra local infrastructure; the cache table is created with `createcachetable` (part of local deploy/setup).
- Define sane TTLs per use — short by default. On `DatabaseCache`, also set explicit `MAX_ENTRIES`/`CULL_FREQUENCY` so the table cannot grow unbounded. Cache keys follow [[GLOSSARY]] naming.
- Django sessions stay DB-backed ([[AUTH]]); Valkey is the application/shared-cache store, not the session store, unless a later decision moves sessions.

## Layer 3 — per-process (narrow use)

- `LocMemCache` exists as a **secondary alias** for hot, staleness-tolerant lookups only (e.g. site flags read on every request).
- Limitation, stated plainly: **each Fargate task has its own copy** — no invalidation propagates between tasks. Never put anything here whose staleness across tasks would be user-visible as inconsistency.
- Example: `apps/m365/graph.py` caches resolved workbook cell values in a module-level dict keyed by cell address, 60s TTL — staleness-tolerant, read-heavy, no cross-task consistency requirement.

## Layer 4 — Astro

- Prefer **prerendering / static output** for pages that do not need SSR; a page that can be static never spends a container cycle.
- SSR responses set explicit `Cache-Control` per route ([[FRONTEND]]).
