"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-02-initial-stack]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Minimal URLconf for config.settings_verify (feedlot apps only)."""

from django.urls import include, path

urlpatterns = [
    path("api/", include("apps.clients.urls")),
    path("api/", include("apps.ledger.urls")),
    path("api/", include("apps.livestock.urls")),
    path("api/", include("apps.feed.urls")),
    path("api/", include("apps.sanitary.urls")),
    path("api/", include("apps.metrics.urls")),
    path("api/", include("apps.market.urls")),
    path("api/", include("apps.advisors.urls")),
]
