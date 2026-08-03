"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.feedyard import views

router = DefaultRouter()
router.register("pens", views.PenViewSet, basename="pen")
router.register("rations", views.RationViewSet, basename="ration")
router.register("loading-orders", views.LoadingOrderViewSet, basename="loading-order")
router.register("bunk-scores", views.BunkScoreViewSet, basename="bunk-score")
router.register("pen-placements", views.PenPlacementViewSet, basename="pen-placement")

urlpatterns = router.urls
