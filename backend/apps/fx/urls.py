"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.fx.views import FxRateViewSet

router = DefaultRouter()
router.register("fx-rates", FxRateViewSet, basename="fx-rate")

urlpatterns = router.urls
