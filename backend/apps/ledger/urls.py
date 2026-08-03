"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.ledger import views

router = DefaultRouter()
router.register("ledger-entries", views.LedgerEntryViewSet, basename="ledgerentry")
router.register("payments", views.PaymentViewSet, basename="payment")
router.register(
    "payment-allocations", views.PaymentAllocationViewSet, basename="paymentallocation"
)

urlpatterns = router.urls
