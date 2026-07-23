"""Scheduled price ingest. Run daily (Cañuelas) / monthly (IPCVA) via cron/beat.

Per-source isolation is the whole point: if one source is down or changed its
HTML, this logs the failure and moves on. A broken source must never leave the
system without the prices it *could* have fetched.
"""

from django.core.management.base import BaseCommand

from apps.market.connectors.base import ConnectorError
from apps.market.models import MarketSource
from apps.market.services import ingest_source


class Command(BaseCommand):
    help = "Ingest reference prices from every active automated source."

    def add_arguments(self, parser):
        parser.add_argument("--source", help="Ingest only this source slug.")
        parser.add_argument("--date", help="Target date YYYY-MM-DD (default: connector's own).")

    def handle(self, *args, **options):
        from datetime import date

        sources = MarketSource.objects.filter(is_active=True, is_automated=True)
        if options.get("source"):
            sources = sources.filter(slug=options["source"])

        target = date.fromisoformat(options["date"]) if options.get("date") else None

        failures = 0
        for source in sources:
            try:
                result = ingest_source(source=source, target_date=target)
                self.stdout.write(self.style.SUCCESS(result.summary))
            except ConnectorError as exc:
                failures += 1
                self.stderr.write(self.style.WARNING(f"{source.slug}: FALLÓ — {exc}"))

        if failures:
            self.stderr.write(self.style.WARNING(f"{failures} fuente(s) fallaron; el resto siguió."))
