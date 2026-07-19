"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

from django.apps import AppConfig


class M365Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.m365"
