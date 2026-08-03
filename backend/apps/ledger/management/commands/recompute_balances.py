"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Rebuild Account.balance_cached from ledger entries (adr-25 rule 2).

Operational repair for a drifted read cache (#14 / #57). Thin wrapper around
`recompute_balance` — one account or all.
"""

from django.core.management.base import BaseCommand, CommandError

from apps.clients.models import Account
from apps.ledger.services import recompute_balance


class Command(BaseCommand):
    help = "Recompute Account.balance_cached from immutable ledger entries."

    def add_arguments(self, parser):
        parser.add_argument(
            "--account",
            type=int,
            help="Account pk to repair; omit to recompute every account.",
        )

    def handle(self, *args, **options):
        qs = Account.objects.all().order_by("pk")
        account_id = options.get("account")
        if account_id is not None:
            qs = qs.filter(pk=account_id)
            if not qs.exists():
                raise CommandError(f"Account {account_id} does not exist.")

        count = 0
        for account in qs:
            balance = recompute_balance(account)
            account.balance_cached = balance
            account.save(update_fields=["balance_cached", "updated_at"])
            self.stdout.write(f"account {account.pk}: {balance}")
            count += 1

        self.stdout.write(self.style.SUCCESS(f"recomputed {count} account(s)"))
