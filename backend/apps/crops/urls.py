"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.crops import views

router = DefaultRouter()
router.register("pivots", views.PivotViewSet, basename="pivot")
router.register("crops", views.CropViewSet, basename="crop")
router.register("cuttings", views.CuttingViewSet, basename="cutting")
router.register("field-tasks", views.FieldTaskViewSet, basename="field-task")

urlpatterns = router.urls
