from rest_framework.routers import DefaultRouter

from apps.ledger import views

router = DefaultRouter()
router.register("ledger-entries", views.LedgerEntryViewSet, basename="ledgerentry")
router.register("payments", views.PaymentViewSet, basename="payment")

urlpatterns = router.urls
