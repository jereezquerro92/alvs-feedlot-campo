"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.breeding.views import (
    CalvingViewSet,
    IatfProtocolStepViewSet,
    IatfProtocolViewSet,
    PregnancyCheckViewSet,
    ServiceViewSet,
    WeaningViewSet,
)

router = DefaultRouter()
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"pregnancy-checks", PregnancyCheckViewSet, basename="pregnancycheck")
router.register(r"calvings", CalvingViewSet, basename="calving")
router.register(r"weanings", WeaningViewSet, basename="weaning")
router.register(r"iatf-protocols", IatfProtocolViewSet, basename="iatfprotocol")
router.register(
    r"iatf-protocol-steps", IatfProtocolStepViewSet, basename="iatfprotocolstep"
)

urlpatterns = router.urls
