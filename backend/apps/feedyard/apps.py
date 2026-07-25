"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

from django.apps import AppConfig


class FeedyardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.feedyard"
    verbose_name = "Corral operativo (corrales / raciones / comedero)"
