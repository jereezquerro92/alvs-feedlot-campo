"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-02-initial-stack]] · [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.health.urls")),
    path("api/", include("apps.users.api_urls")),
    path("accounts/", include("apps.users.urls")),
    path("api/", include("apps.m365.urls")),
    path("api/", include("apps.router.urls")),
]
