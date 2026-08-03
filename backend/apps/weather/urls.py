"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework.routers import DefaultRouter

from apps.weather.views import WeatherLogViewSet

router = DefaultRouter()
router.register("weather-logs", WeatherLogViewSet, basename="weather-log")

urlpatterns = router.urls
