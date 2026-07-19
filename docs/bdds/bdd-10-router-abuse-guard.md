---
created: '2026-07-18'
status: draft
tags:
- bdd
- chatui
- router
- abuse
title: bdd-10-router-abuse-guard
type: bdd
---

# bdd-10 — router abuse guard

## Use case

As a **ChatUI user** sending normal, human-paced messages, when I use the router I never notice a delay beyond the shortened, configurable cooldown ([[GLOSSARY]]: cooldown). As an **automated or scripted caller** hammering the router well above a human pace, when my average messages-per-minute crosses a configurable threshold, the router silently stops answering me for a bounded window — with no error text explaining why — so a burst is contained without teaching an attacker the exact detection rule (#371).

## Scenarios

### Normal cadence is unaffected

```gherkin
Given the per-user cooldown `THROTTLE_COOLDOWN_SECONDS` is at its default (2s)
When an authorized user posts two utterances 3 seconds apart
Then both requests succeed and no abuse evaluation ever runs a threshold check (idle gap exceeds `ROUTER_RATE_IDLE_SKIP_SECONDS`, default 20s)
```

### A sustained burst is silently blocked

```gherkin
Given the user keeps posting inside the idle window continuously
When their average messages-per-minute crosses `ROUTER_RATE_THRESHOLD_PER_MINUTE` (default 20)
Then the async rate-abuse evaluation ([[adr-16-async-mandatory]]) marks the user blocked for `ROUTER_RATE_BLOCK_SECONDS` (default 300)
And every request from that user during the block returns a generic `429` with no distinguishing detail — never a message naming the rule, the threshold, or the remaining time
```

### The block expires on its own

```gherkin
Given a user was silently blocked
When `ROUTER_RATE_BLOCK_SECONDS` elapses
Then their next request is evaluated normally again, with no manual reset required
```

## Frontend half

None visible by design — this is a backend-only enforcement layer. The ChatUI ([[COMPONENTIZATION]]) makes no distinction in its rendering between a generic `429` from the existing cooldown throttle and one from the new silent block; both already degrade the same way in the chat surface (message not sent, retry later). No `PUBLIC_*` variable is added ([[VARIABLES]]), no new island, no new HTMX fragment.

## Backend half

Feeds a new [[TDD]] entry covering `POST /api/router/route/` ([[API]]): the lowered `THROTTLE_COOLDOWN_SECONDS` default, and a new async, DB-cache-backed (no Redis, [[adr-06-cache]]) rate-abuse evaluation fired at the end of the existing async `RouteView` handler ([[adr-16-async-mandatory]]). No new endpoint row — the same `POST /api/router/route/` row gains a documented `429` branch.

## Error handling

A blocked user's request returns a generic `429` with an empty/minimal body — the same status family as the existing `CooldownThrottle` reject, deliberately indistinguishable from it so the specific trigger is never revealed. `Cache-Control: no-store` throughout, unchanged from the existing contract ([[CACHE]]).

## Shadow-test spec

- Post two utterances 3s apart as an authorized user → both succeed.
- Script a burst above 20 msg/min for over a minute → subsequent requests return `429` with no explanatory body, for up to 5 minutes.
- Wait out the block window → the next request is evaluated normally again.
- Until a project's shadow-test runner exists, this entry may reach `building`, never `shipped` ([[BDD]]).
