from django.apps import AppConfig


class ClientsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.clients"

    def ready(self):
        from apps.clients import signals  # noqa: F401
