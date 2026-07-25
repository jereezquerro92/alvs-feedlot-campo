from rest_framework.routers import DefaultRouter

from apps.traceability.views import (
    CaravanaViewSet,
    EstablishmentViewSet,
    TransitDocumentViewSet,
)

router = DefaultRouter()
router.register("establishments", EstablishmentViewSet, basename="establishment")
router.register("transit-documents", TransitDocumentViewSet, basename="transit-document")
router.register("caravanas", CaravanaViewSet, basename="caravana")

urlpatterns = router.urls
