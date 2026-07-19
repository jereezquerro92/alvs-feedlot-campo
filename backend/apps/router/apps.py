"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

from django.apps import AppConfig


class RouterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.router"
