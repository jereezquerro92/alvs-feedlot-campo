---
title: adr-06-cache
type: adr
status: active
created: 2026-07-10
tags: [adr, cache]
---

# ADR-06 — cache

Rules only; content lives in [[CACHE]].

1. No cache server, ever. Redis and ElastiCache are prohibited; the stack must never grow one. Do not add them, do not depend on packages that require them.
2. The four layers defined in [[CACHE]] — HTTP, Django shared cache, per-process, Astro — are the whole strategy. No caching mechanism exists outside them.
3. Every response the containers emit carries an explicit `Cache-Control` header; an absent header is a bug, not a default.
4. Authenticated responses are `no-store` by default; caching personalized data is an opt-in, row-level decision in [[API]] — never a blanket policy.
