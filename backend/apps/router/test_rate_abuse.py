"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

"""Tests for the router's silent rate-abuse guard (#371, tdd-04-router-abuse-guard).

State lives entirely in the shared Django cache ([[CACHE]] layer 2 —
[[adr-06-cache]]). These tests exercise the pure cache-backed module
directly; RouteView wiring is covered in test_route_view.py.
"""

import time

import pytest
from django.core.cache import cache
from django.core.management import call_command

from apps.router.rate_abuse import evaluate_rate_abuse, is_rate_blocked

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _cache_table():
    call_command("createcachetable")
    cache.clear()


def test_first_touch_never_blocks(settings):
    settings.ROUTER_RATE_IDLE_SKIP_SECONDS = 20
    settings.ROUTER_RATE_THRESHOLD_PER_MINUTE = 20
    evaluate_rate_abuse(user_id=1)
    assert is_rate_blocked(user_id=1) is False


def test_idle_gap_skips_entirely_and_resets_streak(settings, monkeypatch):
    settings.ROUTER_RATE_IDLE_SKIP_SECONDS = 20
    settings.ROUTER_RATE_THRESHOLD_PER_MINUTE = 1  # trivially low, would trip if evaluated

    now = [1_000_000.0]
    monkeypatch.setattr("apps.router.rate_abuse._now", lambda: now[0])

    evaluate_rate_abuse(user_id=2)
    now[0] += 25  # exceeds the 20s idle window
    evaluate_rate_abuse(user_id=2)

    assert is_rate_blocked(user_id=2) is False


def test_sustained_burst_crosses_threshold_and_blocks(settings, monkeypatch):
    settings.ROUTER_RATE_IDLE_SKIP_SECONDS = 20
    settings.ROUTER_RATE_THRESHOLD_PER_MINUTE = 20
    settings.ROUTER_RATE_BLOCK_SECONDS = 300

    now = [2_000_000.0]
    monkeypatch.setattr("apps.router.rate_abuse._now", lambda: now[0])

    # 25 calls, 1 second apart -> well above 20/min once the streak has run a minute.
    for _ in range(25):
        evaluate_rate_abuse(user_id=3)
        now[0] += 1

    assert is_rate_blocked(user_id=3) is True


# The block's TTL is real wall-clock (see `_now` in rate_abuse.py: faking the
# clock deliberately leaves the cache backend's own TTL bookkeeping alone), so
# the two halves of "a block is set, and it later expires" cannot be asserted
# against the same short duration — the read-back would race the expiry. They
# are split: the block is asserted live under a TTL too wide to race, and the
# expiry under the short one, without re-asserting the live state (an early
# expiry still satisfies the `is False` this one checks).
def test_block_is_set_when_the_threshold_is_crossed(settings, monkeypatch):
    settings.ROUTER_RATE_IDLE_SKIP_SECONDS = 20
    settings.ROUTER_RATE_THRESHOLD_PER_MINUTE = 1
    settings.ROUTER_RATE_BLOCK_SECONDS = 300

    now = [3_000_000.0]
    monkeypatch.setattr("apps.router.rate_abuse._now", lambda: now[0])

    evaluate_rate_abuse(user_id=4)
    now[0] += 1
    evaluate_rate_abuse(user_id=4)  # crosses threshold=1/min trivially -> blocked
    assert is_rate_blocked(user_id=4) is True


def test_block_expires_after_configured_duration(settings, monkeypatch):
    settings.ROUTER_RATE_IDLE_SKIP_SECONDS = 20
    settings.ROUTER_RATE_THRESHOLD_PER_MINUTE = 1
    settings.ROUTER_RATE_BLOCK_SECONDS = 1

    now = [3_100_000.0]
    monkeypatch.setattr("apps.router.rate_abuse._now", lambda: now[0])

    evaluate_rate_abuse(user_id=7)
    now[0] += 1
    evaluate_rate_abuse(user_id=7)  # crosses threshold=1/min trivially -> blocked

    time.sleep(1.2)  # real TTL expiry (cache backend honors wall-clock TTL)
    assert is_rate_blocked(user_id=7) is False


def test_two_users_never_share_streak_or_block(settings, monkeypatch):
    settings.ROUTER_RATE_IDLE_SKIP_SECONDS = 20
    settings.ROUTER_RATE_THRESHOLD_PER_MINUTE = 1
    settings.ROUTER_RATE_BLOCK_SECONDS = 300

    now = [4_000_000.0]
    monkeypatch.setattr("apps.router.rate_abuse._now", lambda: now[0])

    evaluate_rate_abuse(user_id=5)
    now[0] += 1
    evaluate_rate_abuse(user_id=5)
    assert is_rate_blocked(user_id=5) is True
    assert is_rate_blocked(user_id=6) is False
