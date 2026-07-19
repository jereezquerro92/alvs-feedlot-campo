"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from django.urls import path

from apps.health.views import HealthCheckView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
]
