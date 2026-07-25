from rest_framework.routers import DefaultRouter

from apps.weather.views import WeatherLogViewSet

router = DefaultRouter()
router.register("weather-logs", WeatherLogViewSet, basename="weather-log")

urlpatterns = router.urls
