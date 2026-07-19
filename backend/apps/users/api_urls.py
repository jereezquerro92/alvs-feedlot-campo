"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]] · [[adr-03-api-and-backend]]
Docs: [[BACKEND]] · [[AUTH]]
API: [[API]]
LIVE-DOC:END"""

from django.urls import path

from apps.users import views

urlpatterns = [
    path("me/", views.MeView.as_view(), name="me"),
    path("restricted/", views.RestrictedView.as_view(), name="restricted"),
]
