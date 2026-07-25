"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.sanitary import views

router = DefaultRouter()
router.register("health-products", views.HealthProductViewSet, basename="health-product")
router.register("health-events", views.HealthEventViewSet, basename="health-event")

urlpatterns = router.urls
