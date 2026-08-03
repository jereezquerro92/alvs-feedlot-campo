"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]] · [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]] · [[CHATBOT]]
API: [[API]]
LIVE-DOC:END"""

from django.urls import path

from apps.router import views

urlpatterns = [
    path("router/route/", views.RouteView.as_view(), name="router-route"),
]
