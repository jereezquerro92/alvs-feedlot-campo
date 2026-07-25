from rest_framework.routers import DefaultRouter

from apps.fx.views import FxRateViewSet

router = DefaultRouter()
router.register("fx-rates", FxRateViewSet, basename="fx-rate")

urlpatterns = router.urls
