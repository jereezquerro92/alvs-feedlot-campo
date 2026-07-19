"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

import os

from django.core.management.base import BaseCommand

from apps.users.models import User

BOOTSTRAP_SUB = "bootstrap-admin"


class Command(BaseCommand):
    help = "Idempotently creates or updates the bootstrap superuser from env vars."

    def handle(self, *args, **options):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "bootstrap_admin: DJANGO_SUPERUSER_EMAIL/DJANGO_SUPERUSER_PASSWORD not set, skipping"
                )
            )
            return

        user, _ = User.objects.get_or_create(
            sub=BOOTSTRAP_SUB,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        user.set_password(password)
        user.save()
        self.stdout.write("bootstrap_admin: superuser ready")
