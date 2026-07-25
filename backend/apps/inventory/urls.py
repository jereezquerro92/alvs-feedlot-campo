from rest_framework.routers import DefaultRouter

from apps.inventory.views import InputStockMovementViewSet, InputTypeViewSet

router = DefaultRouter()
router.register("input-types", InputTypeViewSet, basename="input-type")
router.register("input-movements", InputStockMovementViewSet, basename="input-movement")

urlpatterns = router.urls
