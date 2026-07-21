from rest_framework.routers import DefaultRouter

from apps.livestock import views

router = DefaultRouter()
router.register("animals", views.AnimalViewSet, basename="animal")
router.register("lots", views.LotViewSet, basename="lot")
router.register("intakes", views.IntakeViewSet, basename="intake")

urlpatterns = router.urls
