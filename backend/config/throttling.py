"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-06-cache]] · [[adr-02-initial-stack]]
Docs: [[BACKEND]] · [[CACHE]]
LIVE-DOC:END"""

from django.conf import settings
from rest_framework.throttling import UserRateThrottle


class CooldownThrottle(UserRateThrottle):
    scope = "cooldown"

    def __init__(self):
        self.duration = int(settings.THROTTLE_COOLDOWN_SECONDS or 0)
        self.num_requests = 1
        self.rate = f"1/{self.duration}s" if self.duration > 0 else None

    def allow_request(self, request, view):
        if self.duration <= 0:
            return True
        return super().allow_request(request, view)
