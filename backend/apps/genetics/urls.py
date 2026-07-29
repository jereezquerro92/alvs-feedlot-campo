"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.genetics import views

router = DefaultRouter()
router.register("sires", views.SireViewSet, basename="sire")
router.register("breeding-values", views.BreedingValueViewSet, basename="breeding-value")
router.register("semen-batches", views.SemenBatchViewSet, basename="semen-batch")
router.register("semen-movements", views.SemenMovementViewSet, basename="semen-movement")
router.register("semen-sales", views.SemenSaleViewSet, basename="semen-sale")
router.register("embryo-batches", views.EmbryoBatchViewSet, basename="embryo-batch")
router.register("embryo-movements", views.EmbryoMovementViewSet, basename="embryo-movement")
router.register("embryo-flushes", views.EmbryoFlushViewSet, basename="embryo-flush")

urlpatterns = router.urls
