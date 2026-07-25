"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.traceability.views import (
    CaravanaViewSet,
    EstablishmentViewSet,
    TransitDocumentViewSet,
)

router = DefaultRouter()
router.register("establishments", EstablishmentViewSet, basename="establishment")
router.register("transit-documents", TransitDocumentViewSet, basename="transit-document")
router.register("caravanas", CaravanaViewSet, basename="caravana")

urlpatterns = router.urls
