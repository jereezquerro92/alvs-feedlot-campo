"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from django.urls import path

from apps.m365 import views

app_name = "m365"

urlpatterns = [
    path("m365/hello/", views.HelloView.as_view(), name="hello"),
    path("m365/world/", views.WorldView.as_view(), name="world"),
]
