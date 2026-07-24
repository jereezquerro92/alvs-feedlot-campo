from rest_framework.routers import DefaultRouter

from apps.advisors import views

router = DefaultRouter()
router.register("advisors", views.AdvisorViewSet, basename="advisor")
router.register("advisor-reports", views.AdvisorReportViewSet, basename="advisor-report")

urlpatterns = router.urls
