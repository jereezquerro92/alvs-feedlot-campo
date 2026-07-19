---
title: tdd-04-router-abuse-guard
type: tdd
status: green
api: ["POST /api/router/route/"]
created: 2026-07-18
tags: [tdd, router, abuse, cache]
---

# tdd-04 — router abuse guard

## Context

Closes #371 ([[bdd-10-router-abuse-guard]]). The existing `CooldownThrottle` default (30s) is too aggressive for normal ChatUI use; this entry lowers it and adds a second, independent layer: an async, silent rate-abuse block on `POST /api/router/route/` ([[API]]) that only engages during a sustained burst, never during normal, human-paced use.

## Design

- **Cooldown default lowered**: `THROTTLE_COOLDOWN_SECONDS` default `30` → `2` ([[VARIABLES]]). No code change to `CooldownThrottle` itself — same class, same mechanism ([[CACHE]] layer 2).
- **New module** `backend/apps/router/rate_abuse.py` — `evaluate_rate_abuse(user_id)` and `is_rate_blocked(user_id)`. State lives entirely in the shared `DatabaseCache` ([[CACHE]], [[adr-06-cache]] — no Redis): one cache key per user for the current activity streak (`start`, `count`, `last`), one cache key per user for an active block (present ⇒ blocked, TTL = `ROUTER_RATE_BLOCK_SECONDS`).
- **Idle-skip**: if there is no cached streak for the user, or the gap since the last recorded activity exceeds `ROUTER_RATE_IDLE_SKIP_SECONDS` (default 20), the streak resets to a fresh start (count=1) and **no threshold check runs** — this is the "evaluates nothing" branch and is the common case.
- **Rate check**: otherwise the streak's count increments and its average messages-per-minute (`count / elapsed_minutes_since_streak_start`) is compared to `ROUTER_RATE_THRESHOLD_PER_MINUTE` (default 20). Crossing it sets the block key with TTL `ROUTER_RATE_BLOCK_SECONDS` (default 300).
- **Wiring in `RouteView.post`** ([[adr-16-async-mandatory]]): `is_rate_blocked` is checked first (via `sync_to_async`, cheap single cache read) — a blocked user gets a bare `429` immediately, audited `choice="rate_blocked"`, zero inference calls. `evaluate_rate_abuse` is fired via `sync_to_async` at the very end of a successful pass (after the outcome is computed, before the response is returned) so it never delays the response body construction and never runs for a request that was already rejected upstream (disabled/hard-reject/unavailable/throttled/permission-denied paths do not update the streak — only a request that reached inference does).
- **Why cache, not a new model**: the state is transient, per-user, TTL-bounded by design (a stale streak past the idle window is meaningless) — exactly what `DatabaseCache` is for ([[CACHE]] layer 2), and it avoids a migration for data with no audit value (the existing `IntentQuery` audit trail already covers durable history).
- **Why not reuse `IntentQuery.created_at`**: coupling the abuse guard to the audit table would tie its behavior to `ROUTER_AUDIT_RETENTION_DAYS` purges and require a DB query per evaluation instead of a single cache read; the two concerns (audit retention vs. rate enforcement) stay decoupled.

## Tests (`backend/apps/router/test_rate_abuse.py`, `backend/apps/router/test_route_view.py`, `backend/config/test_throttling.py`)

- `test_rate_abuse.py`:
  - idle/first-touch evaluation does not block and does not raise even at count=1.
  - a burst of calls within the idle window that crosses the per-minute threshold sets the block.
  - once blocked, `is_rate_blocked` returns `True` until the block TTL expires (simulated via a monkeypatched clock).
  - two different users never share a streak or a block (cache key isolation).
  - a gap longer than `ROUTER_RATE_IDLE_SKIP_SECONDS` resets the streak instead of accumulating toward the threshold.
- `test_route_view.py` (new cases): a user already marked rate-blocked gets a bare `429` with no body detail and no inference call; the audit row records `choice="rate_blocked"`.
- `test_throttling.py`: unchanged — cooldown mechanism itself did not change, only its configured default (asserted via the existing settings-driven tests, which set the value explicitly per test and are therefore unaffected by the default change).

## Status

`draft → red → green`. Tests were written first (red: `ModuleNotFoundError` / `AttributeError` for `apps.router.rate_abuse`), then `rate_abuse.py` was implemented and `RouteView`/`settings.py` wired until the full `backend/apps/router/` and `backend/config/` suites passed green.
