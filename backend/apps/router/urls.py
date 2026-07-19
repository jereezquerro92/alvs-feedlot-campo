"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]] · [[adr-03-api-and-backend]]
Docs: [[BACKEND]] · [[CHATBOT]]
API: [[API]]
LIVE-DOC:END"""

from django.urls import path

from apps.router import views

urlpatterns = [
    path("router/route/", views.RouteView.as_view(), name="router-route"),
]
