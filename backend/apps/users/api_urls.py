"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]] · [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]] · [[AUTH]]
API: [[API]]
LIVE-DOC:END"""

from django.urls import path

from apps.users import views

urlpatterns = [
    path("me/", views.MeView.as_view(), name="me"),
    path("restricted/", views.RestrictedView.as_view(), name="restricted"),
]
