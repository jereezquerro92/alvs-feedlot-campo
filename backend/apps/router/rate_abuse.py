"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

"""The router's silent rate-abuse guard (#371, tdd-04-router-abuse-guard).

Enforcement only — never authorization ([[adr-15-chatbot-two-tier]] rule 3).
All state lives in the shared `DatabaseCache` ([[CACHE]] layer 2); no Redis
([[adr-06-cache]]). Two cache keys per user:

- a "streak" (start/count/last) tracking a contiguous run of router activity,
  reset whenever the gap since the last touch exceeds
  `ROUTER_RATE_IDLE_SKIP_SECONDS` — the reset path evaluates nothing (no
  threshold math), which is the common, human-paced case;
- a "block" marker, present only while the user is silently blocked, with a
  TTL of `ROUTER_RATE_BLOCK_SECONDS`.

Callers: `RouteView` checks `is_rate_blocked` before doing any work, and
fires `evaluate_rate_abuse` (via `sync_to_async`, [[adr-16-async-mandatory]])
once a request has actually reached inference.
"""

import time as _time_module

from django.conf import settings
from django.core.cache import cache

_STREAK_KEY = "router:rate:streak:{user_id}"
_BLOCK_KEY = "router:rate:blocked:{user_id}"


def _now() -> float:
    """Indirection so tests can fake the clock without touching the shared
    stdlib `time` module — patching `time.time` globally would also corrupt
    the cache backend's own TTL bookkeeping, which uses real wall-clock
    time ([[CACHE]] layer 2)."""
    return _time_module.time()


def is_rate_blocked(user_id) -> bool:
    """Cheap single cache read — the only thing a request pays before doing
    any router work."""
    return cache.get(_BLOCK_KEY.format(user_id=user_id)) is not None


def evaluate_rate_abuse(user_id) -> None:
    """Update the user's activity streak and, only when it is live (not
    freshly reset by an idle gap), check it against the configured
    threshold. Never raises; a defect here must never take the router down.
    """
    now = _now()
    key = _STREAK_KEY.format(user_id=user_id)
    streak = cache.get(key)

    idle_skip = settings.ROUTER_RATE_IDLE_SKIP_SECONDS
    streak_ttl = max(idle_skip * 4, 60)

    if streak is None or (now - streak["last"]) > idle_skip:
        # First touch, or the gap since the last one exceeds the idle
        # window: this is the common case and evaluates nothing — no
        # threshold check runs.
        cache.set(key, {"start": now, "count": 1, "last": now}, timeout=streak_ttl)
        return

    count = streak["count"] + 1
    elapsed_minutes = max((now - streak["start"]) / 60.0, 1e-6)
    rate_per_minute = count / elapsed_minutes
    cache.set(key, {"start": streak["start"], "count": count, "last": now}, timeout=streak_ttl)

    if rate_per_minute > settings.ROUTER_RATE_THRESHOLD_PER_MINUTE:
        cache.set(
            _BLOCK_KEY.format(user_id=user_id),
            True,
            timeout=settings.ROUTER_RATE_BLOCK_SECONDS,
        )
