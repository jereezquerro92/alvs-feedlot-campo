"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]] · [[adr-03-api-and-backend]]
Docs: [[BACKEND]] · [[AUTH]]
API: [[API]]
LIVE-DOC:END"""

from django.conf import settings
from django.urls import path

from apps.users import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("callback/", views.CallbackView.as_view(), name="callback"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
]

if settings.DEBUG and settings.AUTH_DEV_MODE:
    urlpatterns.append(
        path("dev-login/", views.DevLoginView.as_view(), name="dev-login")
    )
