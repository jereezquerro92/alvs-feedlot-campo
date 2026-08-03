"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.inventory.views import InputStockMovementViewSet, InputTypeViewSet

router = DefaultRouter()
router.register("input-types", InputTypeViewSet, basename="input-type")
router.register("input-movements", InputStockMovementViewSet, basename="input-movement")

urlpatterns = router.urls
