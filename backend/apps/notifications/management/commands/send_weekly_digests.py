"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Build and send the weekly digest to every active client — per-client isolation.

A failure for one client (missing contact, sender error) is logged and never stops
the batch (adr-36 conseq., same discipline as `ingest_prices`). The `to_address` comes
from the client's `contact` field unless overridden per run.
"""

from django.core.management.base import BaseCommand

from apps.clients.models import Client
from apps.notifications.services import send_weekly_digest


class Command(BaseCommand):
    help = "Send the weekly metrics digest to every active client."

    def add_arguments(self, parser):
        parser.add_argument(
            "--channel", default="whatsapp",
            help="Delivery channel (whatsapp|email). Default whatsapp.",
        )
        parser.add_argument(
            "--client", type=int, default=None,
            help="Restrict to a single client id.",
        )

    def handle(self, *args, **options):
        channel = options["channel"]
        clients = Client.objects.filter(is_active=True)
        if options["client"]:
            clients = clients.filter(id=options["client"])

        sent = failed = skipped = 0
        for client in clients:
            to_address = (client.contact or "").strip()
            if not to_address:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(f"skip {client.name}: no contact address")
                )
                continue
            try:
                notification = send_weekly_digest(
                    client=client, channel=channel, to_address=to_address
                )
            except Exception as exc:  # isolation: one client never stops the batch
                failed += 1
                self.stdout.write(self.style.ERROR(f"fail {client.name}: {exc}"))
                continue

            if notification.status == notification.Status.SENT:
                sent += 1
                self.stdout.write(self.style.SUCCESS(f"sent {client.name}"))
            else:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(f"fail {client.name}: {notification.error}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"done — sent={sent} failed={failed} skipped={skipped}"
            )
        )
