"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

"""`manage.py purge_router_audit [--dry-run]`.

Deletes `IntentQuery` rows older than `ROUTER_AUDIT_RETENTION_DAYS` by
`created_at` ([[CHATBOT]] — Retention, closes #65). Idempotent: running it
twice in a row deletes nothing on the second pass.
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.router.models import IntentQuery


class Command(BaseCommand):
    help = "Delete IntentQuery audit rows older than ROUTER_AUDIT_RETENTION_DAYS."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="report the count that would be deleted without deleting",
        )

    def handle(self, *args, **options):
        retention_days = settings.ROUTER_AUDIT_RETENTION_DAYS
        cutoff = timezone.now() - timezone.timedelta(days=retention_days)
        queryset = IntentQuery.objects.filter(created_at__lt=cutoff)
        count = queryset.count()

        if options["dry_run"]:
            self.stdout.write(f"dry-run: {count} row(s) older than {retention_days} day(s) would be deleted")
            return

        queryset.delete()
        self.stdout.write(f"deleted {count} row(s) older than {retention_days} day(s)")
