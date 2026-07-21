from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.feed import views

router = DefaultRouter()
router.register("feed-types", views.FeedTypeViewSet, basename="feedtype")
router.register("feed-deliveries", views.FeedDeliveryViewSet, basename="feeddelivery")
router.register("feedings", views.FeedingEventViewSet, basename="feeding")

urlpatterns = router.urls + [
    path("feed-stock/", views.feed_stock, name="feed-stock"),
]
