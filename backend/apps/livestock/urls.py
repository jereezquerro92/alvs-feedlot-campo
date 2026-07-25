"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.livestock import views

router = DefaultRouter()
router.register("animals", views.AnimalViewSet, basename="animal")
router.register("lots", views.LotViewSet, basename="lot")
router.register("intakes", views.IntakeViewSet, basename="intake")
# Phase 2 — lifecycle events
router.register("weighings", views.WeighingViewSet, basename="weighing")
router.register("deaths", views.DeathViewSet, basename="death")
router.register("exits", views.ExitViewSet, basename="exit")

urlpatterns = router.urls
