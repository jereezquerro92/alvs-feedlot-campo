from rest_framework.routers import DefaultRouter

from apps.sanitary import views

router = DefaultRouter()
router.register("health-products", views.HealthProductViewSet, basename="health-product")
router.register("health-events", views.HealthEventViewSet, basename="health-event")

urlpatterns = router.urls
