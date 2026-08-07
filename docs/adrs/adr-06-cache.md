---
title: adr-06-cache
type: adr
category: devops
use_case: adding any caching mechanism, writing a response that might skip Cache-Control, caching personalized or authenticated data, provisioning or resizing the shared cache
created: 2026-07-10
modified: 2026-08-07
tags: [adr, cache]
---

# ADR-06 — cache

## CONTEXT

> The shared Django cache in cloud is ElastiCache Valkey; four layers are the whole cache strategy; no response leaves without a `Cache-Control` header.

## ASSERTIONS

1. The sanctioned cloud shared-cache server is AWS ElastiCache **Valkey**, sized and placed as [[CACHE]] and [[INFRASTRUCTURE]] state. Until measured traffic requires more, the pick is `cache.t4g.micro`, single-node, no Multi-AZ. Unmanaged Redis, a second cache product, or a larger/HA topology without that traffic proof is out of scope.
2. The four layers defined in [[CACHE]] — HTTP, Django shared cache, per-process, Astro — are the whole strategy. No caching mechanism exists outside them. Layer 2 in cloud is Valkey; locally it is `DatabaseCache` ([[DOCKER]]).
3. Every response the containers emit carries an explicit `Cache-Control` header; an absent header is a bug, not a default.
4. Authenticated responses are `no-store` by default; caching personalized data is an opt-in, row-level decision in [[API]] — never a blanket policy.

## FORBIDDEN

- **NEVER** add unmanaged Redis, a non-Valkey ElastiCache engine, Multi-AZ / replica Valkey, or a node class above the [[CACHE]] pick without an owner traffic-justified resize of that pick (rule 1). The Valkey node is the one sanctioned cache server, not an open Redis door.
- **NEVER** ship a response with no explicit `Cache-Control` header (rule 3), whatever the framework would default to.
- **NEVER** cache an authenticated response by blanket policy (rule 4). `no-store` is overridden per row in [[API]], never globally.

## REJECTED

- **No cache server, ever** — the policy this ADR held until 2026-08-07: Redis and ElastiCache were prohibited outright and layer 2 was `DatabaseCache` in every environment. It kept Fargate cost and ops minimal, but blocked a shared in-memory cache across tasks and left Channels-class fan-out permanently closed. Replaced by rule 1's Valkey pick (`cache.t4g.micro`, single-node, no Multi-AZ until traffic justifies more) and by loosening the harness skills that enforced the prohibition. It would reopen only if Valkey cost or ops burden outweighed the shared-cache need and the owner withdrew the pick.

## RELATED

### related adrs

- [[docs/adrs/adr-50-initial-stack]] — rule 4, the stack-level echo of rule 1
- [[docs/adrs/adr-09-docker-compose]] — local layer 2 stays `DatabaseCache`
- [[docs/adrs/adr-16-async-mandatory]] — Valkey for Django cache does not by itself authorize Channels

### related files

- [[docs/CACHE]] — the four layers, Valkey sizing, and local vs cloud backends
- [[docs/constitution/INFRASTRUCTURE]] — ElastiCache placement and security groups
- [[docs/API]] — where a per-route caching exception is declared
- [[docs/VARIABLES]] — cache connection env names
