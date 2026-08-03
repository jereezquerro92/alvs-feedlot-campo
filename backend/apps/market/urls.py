"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.market import views

router = DefaultRouter()
router.register("market-sources", views.MarketSourceViewSet, basename="market-source")
router.register("market-prices", views.MarketPriceViewSet, basename="market-price")

urlpatterns = router.urls
