"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.weather.views import WeatherLogViewSet

router = DefaultRouter()
router.register("weather-logs", WeatherLogViewSet, basename="weather-log")

urlpatterns = router.urls
