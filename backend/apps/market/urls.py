from rest_framework.routers import DefaultRouter

from apps.market import views

router = DefaultRouter()
router.register("market-sources", views.MarketSourceViewSet, basename="market-source")
router.register("market-prices", views.MarketPriceViewSet, basename="market-price")

urlpatterns = router.urls
