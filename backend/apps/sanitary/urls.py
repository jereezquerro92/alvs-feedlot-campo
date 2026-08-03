"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.sanitary import views

router = DefaultRouter()
router.register("health-products", views.HealthProductViewSet, basename="health-product")
router.register("health-events", views.HealthEventViewSet, basename="health-event")
router.register("sanitary-plans", views.SanitaryPlanViewSet, basename="sanitary-plan")
router.register(
    "sanitary-plan-items", views.SanitaryPlanItemViewSet, basename="sanitary-plan-item"
)
router.register("plan-enrollments", views.PlanEnrollmentViewSet, basename="plan-enrollment")

urlpatterns = router.urls
