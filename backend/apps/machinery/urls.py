"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.machinery import views

router = DefaultRouter()
router.register("machines", views.MachineViewSet, basename="machine")
router.register(
    "maintenance-events", views.MaintenanceEventViewSet, basename="maintenance-event"
)

urlpatterns = router.urls
