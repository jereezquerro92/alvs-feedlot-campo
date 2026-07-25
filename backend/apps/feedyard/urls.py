from rest_framework.routers import DefaultRouter

from apps.feedyard import views

router = DefaultRouter()
router.register("pens", views.PenViewSet, basename="pen")
router.register("rations", views.RationViewSet, basename="ration")
router.register("loading-orders", views.LoadingOrderViewSet, basename="loading-order")
router.register("bunk-scores", views.BunkScoreViewSet, basename="bunk-score")

urlpatterns = router.urls
