from rest_framework.routers import DefaultRouter

from apps.machinery import views

router = DefaultRouter()
router.register("machines", views.MachineViewSet, basename="machine")
router.register(
    "maintenance-events", views.MaintenanceEventViewSet, basename="maintenance-event"
)

urlpatterns = router.urls
