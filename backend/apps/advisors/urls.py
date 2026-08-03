"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.advisors import views

router = DefaultRouter()
router.register("advisors", views.AdvisorViewSet, basename="advisor")
router.register("advisor-reports", views.AdvisorReportViewSet, basename="advisor-report")

urlpatterns = router.urls
