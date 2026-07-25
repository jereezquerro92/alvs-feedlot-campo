"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.advisors import views

router = DefaultRouter()
router.register("advisors", views.AdvisorViewSet, basename="advisor")
router.register("advisor-reports", views.AdvisorReportViewSet, basename="advisor-report")

urlpatterns = router.urls
