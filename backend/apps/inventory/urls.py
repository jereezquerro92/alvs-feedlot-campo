"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.inventory.views import InputStockMovementViewSet, InputTypeViewSet

router = DefaultRouter()
router.register("input-types", InputTypeViewSet, basename="input-type")
router.register("input-movements", InputStockMovementViewSet, basename="input-movement")

urlpatterns = router.urls
