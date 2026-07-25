from rest_framework.routers import DefaultRouter

from apps.assistant import views

router = DefaultRouter()
router.register("conversations", views.ConversationViewSet, basename="conversation")

urlpatterns = router.urls
