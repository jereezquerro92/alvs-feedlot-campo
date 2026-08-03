"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-50-initial-stack]] · [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
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
    # Feedlot domain (Phase 1) — docs/FEEDLOT.md, docs/API.md
    path("api/", include("apps.clients.urls")),
    path("api/", include("apps.ledger.urls")),
    path("api/", include("apps.livestock.urls")),
    path("api/", include("apps.feed.urls")),
    path("api/", include("apps.sanitary.urls")),
    path("api/", include("apps.metrics.urls")),
    path("api/", include("apps.market.urls")),
    path("api/", include("apps.advisors.urls")),
    # Feedlot multi-rubro (Phase 6) — docs/adrs/adr-32-multi-rubro-assets.md, docs/API.md
    path("api/", include("apps.crops.urls")),
    path("api/", include("apps.machinery.urls")),
    # Extra expenses (labor/fuel/machinery "carga de deudas") — docs/adrs/adr-44-field-operational-roles.md, docs/API.md
    path("api/", include("apps.expenses.urls")),
    # Feedlot pen operating loop (Phase 7) — docs/adrs/adr-33-feedyard-operating-loop.md, docs/API.md
    path("api/", include("apps.feedyard.urls")),
    # Conversational assistant (Phase 8) — docs/adrs/adr-35-conversational-assistant.md, docs/API.md
    path("api/", include("apps.assistant.urls")),
    path("api/", include("apps.notifications.urls")),
    path("api/", include("apps.inventory.urls")),
    path("api/", include("apps.weather.urls")),
    # SENASA traceability (Phase 11) — docs/adrs/adr-38-senasa-traceability.md, docs/API.md
    path("api/", include("apps.traceability.urls")),
    # Gross margin & reference FX (Phase 12) — docs/adrs/adr-39-gross-margin-and-fx.md, docs/API.md
    path("api/", include("apps.fx.urls")),
    # Cría y recría (genética + reproducción) — docs/adrs/adr-46, adr-47, docs/API.md
    path("api/", include("apps.genetics.urls")),
    path("api/", include("apps.breeding.urls")),
]
