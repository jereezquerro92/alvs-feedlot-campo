"""Seed realistic demo data for the feedlot domain (local/DEBUG only).

Every operational fact is created through the domain SERVICES, never by raw
INSERT, so the event-sourcing invariants hold: each own-stock ration posts its
ledger debit and stock movement (adr-25 rule 4), each weighing updates the
derived weight, deaths/exits maintain lot counters and never touch the ledger
(adr-28 rule 3). Catalogs (FeedType, HealthProduct, MarketPrice) are the only
editable tables and are created directly.

This is a demo/dev convenience, not production data. It refuses to run outside
DEBUG and `--reset` wipes the domain tables so it stays re-runnable.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.clients.models import Account, Client
from apps.feed.models import FeedType
from apps.feed.services import register_delivery, register_feeding
from apps.feed.models import FeedingEvent
from apps.ledger.services import register_payment
from apps.livestock.models import Animal, Death, Exit, Weighing
from apps.livestock.services import (
    create_individual_intake,
    create_lot_intake,
    register_death,
    register_exit,
    register_weighing,
)
from apps.market.models import MarketPrice, MarketSource
from apps.sanitary.models import HealthProduct
from apps.sanitary.services import register_health_event

DEMO_TAX_IDS = ["DEMO-1", "DEMO-2"]


class Command(BaseCommand):
    help = "Seed demo feedlot data (clients, cattle, feed, health, prices). DEBUG only."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo data before seeding (idempotent re-run).",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo_feedlot only runs with DEBUG=True (dev only).")

        if options["reset"]:
            self._reset()

        if Client.objects.filter(tax_id__in=DEMO_TAX_IDS).exists():
            self.stdout.write(
                self.style.WARNING(
                    "Demo clients already present; pass --reset to rebuild. Nothing to do."
                )
            )
            return

        today = date.today()

        def d(days_ago):
            return today - timedelta(days=days_ago)

        with transaction.atomic():
            feed_types = self._seed_feed_catalog()
            products = self._seed_health_catalog()
            self._seed_client_esperanza(feed_types, products, d)
            self._seed_client_alberto(feed_types, d)
            self._seed_market_prices(d)

        self._report()

    # ------------------------------------------------------------------ reset
    def _reset(self):
        from apps.feed.models import FeedDelivery, FeedStockMovement
        from apps.ledger.models import LedgerEntry, Payment
        from apps.livestock.models import Intake, Lot
        from apps.sanitary.models import HealthEvent

        demo_clients = Client.objects.filter(tax_id__in=DEMO_TAX_IDS)
        client_ids = list(demo_clients.values_list("id", flat=True))
        if not client_ids:
            self.stdout.write("No demo data to reset.")
            return

        # Delete leaf events first, then owning rows. Order matters (PROTECT FKs).
        Weighing.objects.filter(
            models_or(animal__client_id__in=client_ids, lot__client_id__in=client_ids)
        ).delete()
        Death.objects.filter(
            models_or(animal__client_id__in=client_ids, lot__client_id__in=client_ids)
        ).delete()
        Exit.objects.filter(
            models_or(animal__client_id__in=client_ids, lot__client_id__in=client_ids)
        ).delete()
        HealthEvent.objects.filter(client_id__in=client_ids).delete()
        FeedingEvent.objects.filter(client_id__in=client_ids).delete()
        FeedStockMovement.objects.filter(client_id__in=client_ids).delete()
        FeedDelivery.objects.filter(client_id__in=client_ids).delete()
        Payment.objects.filter(account__client_id__in=client_ids).delete()
        LedgerEntry.objects.filter(account__client_id__in=client_ids).delete()
        Animal.objects.filter(client_id__in=client_ids).delete()
        Intake.objects.filter(client_id__in=client_ids).delete()
        Lot.objects.filter(client_id__in=client_ids).delete()
        Account.objects.filter(client_id__in=client_ids).delete()
        demo_clients.delete()
        # Demo market prices ride on the shared canuelas source; drop only ours.
        MarketPrice.objects.filter(raw__demo=True).delete()
        self.stdout.write(self.style.WARNING("Demo data wiped."))

    # --------------------------------------------------------------- catalogs
    def _seed_feed_catalog(self):
        specs = [
            ("Maíz molido", "grano"),
            ("Silaje de maíz", "voluminoso"),
            ("Balanceado engorde", "balanceado"),
        ]
        out = {}
        for name, category in specs:
            ft, _ = FeedType.objects.get_or_create(
                name=name, defaults={"unit": "kg", "category": category}
            )
            out[name] = ft
        return out

    def _seed_health_catalog(self):
        specs = [
            ("Vacuna Aftosa", HealthProduct.Kind.VACCINE, "dosis", "180.0000"),
            ("Antiparasitario", HealthProduct.Kind.ANTIPARASITIC, "dosis", "95.0000"),
        ]
        out = {}
        for name, kind, unit, price in specs:
            hp, _ = HealthProduct.objects.get_or_create(
                name=name,
                defaults={"kind": kind, "unit": unit, "unit_price": Decimal(price)},
            )
            out[name] = hp
        return out

    # ------------------------------------------------------- client 1: boarding
    def _seed_client_esperanza(self, feed, products, d):
        client = Client.objects.create(
            name="Estancia La Esperanza",
            kind=Client.Kind.BOARDING,
            tax_id="DEMO-1",
            contact="Ramiro Paz · 3512-445566",
        )
        # Account is auto-created by the Client post_save signal (apps.clients.signals).

        # Individual intake: 6 steers at ~300 kg, 100 days ago.
        _, animals = create_individual_intake(
            client=client,
            date=d(100),
            animals=[
                {"ear_tag": f"NOV-{i:03d}", "category": "steer", "sex": "male",
                 "entry_weight": Decimal(280 + i * 6)}
                for i in range(1, 7)
            ],
        )

        # Anonymous lot: 50 head, 15000 kg total (300/head), 100 days ago.
        _, lot = create_lot_intake(
            client=client, date=d(100), code="L-2026-01",
            head_count=50, total_weight=Decimal("15000"),
        )

        # Client provides silage (their stock, uncharged when fed).
        register_delivery(
            client=client, feed_type=feed["Silaje de maíz"], quantity=Decimal("25000"), date=d(100),
        )

        # Feedings on the lot: own balanceado (charged) + client silage (uncharged).
        for day, qty in [(90, "2800"), (70, "3000"), (50, "3100"), (30, "3200"), (10, "3000")]:
            register_feeding(
                client=client, feed_type=feed["Balanceado engorde"], quantity=Decimal(qty),
                unit_price=Decimal("245.0000"), origin=FeedingEvent.Origin.OWN_STOCK,
                date=d(day), lot=lot,
            )
        for day, qty in [(85, "4000"), (45, "4200")]:
            register_feeding(
                client=client, feed_type=feed["Silaje de maíz"], quantity=Decimal(qty),
                unit_price=Decimal("60.0000"), origin=FeedingEvent.Origin.CLIENT_STOCK,
                date=d(day), lot=lot,
            )

        # Lot weighings: head_count constant (50) => GDP calculable.
        register_weighing(lot=lot, weight=Decimal("15000"), date=d(100), head_count=50)
        register_weighing(lot=lot, weight=Decimal("16600"), date=d(60), head_count=50)
        register_weighing(lot=lot, weight=Decimal("18100"), date=d(20), head_count=50)

        # Individual animal NOV-001: three weighings + own-stock feeding.
        nov1 = animals[0]
        register_feeding(
            client=client, feed_type=feed["Balanceado engorde"], quantity=Decimal("450"),
            unit_price=Decimal("245.0000"), origin=FeedingEvent.Origin.OWN_STOCK,
            date=d(40), animal=nov1,
        )
        register_weighing(animal=nov1, weight=Decimal("300"), date=d(90))
        register_weighing(animal=nov1, weight=Decimal("360"), date=d(50))
        register_weighing(animal=nov1, weight=Decimal("410"), date=d(20))

        # Health: vaccinate the whole lot (charged) + deworm one animal (charged).
        register_health_event(
            client=client, product=products["Vacuna Aftosa"], quantity=Decimal("50"),
            date=d(95), lot=lot, head_count=50,
        )
        register_health_event(
            client=client, product=products["Antiparasitario"], quantity=Decimal("1"),
            date=d(80), animal=nov1,
        )

        # One death (disease) on NOV-006 — lot GDP stays clean.
        register_death(
            animal=animals[5], date=d(55), cause=Death.Cause.DISEASE,
            cause_detail="Neumonía",
        )

        # Sell NOV-001 (informational price) and 10 head of the lot.
        register_exit(
            animal=nov1, date=d(15), kind=Exit.Kind.SALE, destination="Frigorífico Sur",
            sale_price_per_kg=Decimal("2050.0000"),
        )
        register_exit(
            lot=lot, date=d(10), kind=Exit.Kind.SALE, destination="Remate Cañuelas",
            head_count=10, weight=Decimal("3800"), sale_price_per_kg=Decimal("2100.0000"),
        )

        # A partial payment against the running account.
        register_payment(
            account=client.account, amount=Decimal("1500000"), date=d(40),
            method="transfer", reference="TRF-8842",
        )

    # ----------------------------------------------------------- client 2: own
    def _seed_client_alberto(self, feed, d):
        client = Client.objects.create(
            name="Don Alberto (hacienda propia)",
            kind=Client.Kind.OWN,
            tax_id="DEMO-2",
            contact="interno",
        )
        # Account is auto-created by the Client post_save signal.

        _, lot = create_lot_intake(
            client=client, date=d(70), code="L-2026-02",
            head_count=30, total_weight=Decimal("9000"),
        )
        for day, qty in [(60, "1800"), (35, "1900"), (12, "2000")]:
            register_feeding(
                client=client, feed_type=feed["Maíz molido"], quantity=Decimal(qty),
                unit_price=Decimal("210.0000"), origin=FeedingEvent.Origin.OWN_STOCK,
                date=d(day), lot=lot,
            )
        register_weighing(lot=lot, weight=Decimal("9000"), date=d(70), head_count=30)
        register_weighing(lot=lot, weight=Decimal("10200"), date=d(20), head_count=30)

    # -------------------------------------------------------------- market data
    def _seed_market_prices(self, d):
        source = MarketSource.objects.get(slug="canuelas")
        # A ~2-month daily-ish series, trending up, for two categories.
        series = [
            ("Novillo", 100, "1820"), ("Novillo", 80, "1875"), ("Novillo", 60, "1940"),
            ("Novillo", 40, "1990"), ("Novillo", 20, "2060"), ("Novillo", 5, "2110"),
            ("Vaquillona", 60, "1760"), ("Vaquillona", 30, "1850"), ("Vaquillona", 5, "1920"),
        ]
        for category, days_ago, avg in series:
            price = Decimal(avg)
            MarketPrice.objects.update_or_create(
                source=source, category=category, date=d(days_ago),
                defaults={
                    "price_avg": price,
                    "price_min": price - Decimal("60"),
                    "price_max": price + Decimal("70"),
                    "price_median": price,
                    "head_count": 400,
                    "raw": {"demo": True},
                },
            )

    # ------------------------------------------------------------------ report
    def _report(self):
        lines = [
            "Demo feedlot data seeded:",
            f"  clients          {Client.objects.filter(tax_id__in=DEMO_TAX_IDS).count()}",
            f"  animals          {Animal.objects.count()}",
            f"  market prices    {MarketPrice.objects.filter(raw__demo=True).count()}",
        ]
        for c in Client.objects.filter(tax_id__in=DEMO_TAX_IDS):
            lines.append(f"  · {c.name}: balance ARS {c.account.balance_cached}")
        self.stdout.write(self.style.SUCCESS("\n".join(lines)))


def models_or(**kwargs):
    """Small helper: OR the given lookups into a single Q."""
    from django.db.models import Q

    q = Q()
    for key, value in kwargs.items():
        q |= Q(**{key: value})
    return q
