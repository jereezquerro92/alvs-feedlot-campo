"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

"""`manage.py seed_router_menu` — idempotent upsert of the router starter menu.

The chatui surface is wired end to end, but a router with an empty `Intent`
registry can only answer NO_MATCH/ESCALATE ([[adr-15-chatbot-two-tier]] rule 2).
This command authors the closed starter menu every environment gets (#135):
product destinations, never demo data, never generated text.

No DEBUG gate — prod needs the same starter menu as local, so this is not the
DEBUG-only development path of [[adr-10-auth]] rule 6.
"""

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from apps.router.models import KIND_CONFIRM, KIND_NAVIGATE, Intent
from apps.users.roles import FIELD_MANAGERS

# (phrase, target, kind, group_name, order). Phrases are the Spanish the drawer
# renders ([[LOCALIZATION]]); the code around them stays English.
#
# Every row is gated on `field_managers` except `Cerrar sesión`: a role-less
# session is confined to the lobby, and the only routes standing outside that
# gate are `/accounts/*` and health ([[adr-20-authorization-lobby]] rule 1), so
# logout is the one starter destination it may be offered.
STARTER_MENU = (
    ("Ir al perfil", "/profile/", KIND_NAVIGATE, FIELD_MANAGERS, 10),
    ("Cerrar sesión", "/accounts/logout/", KIND_CONFIRM, None, 20),
    ("Abrir clientes", "/feedlot/", KIND_NAVIGATE, FIELD_MANAGERS, 30),
    ("Ver hacienda", "/feedlot/hacienda", KIND_NAVIGATE, FIELD_MANAGERS, 40),
    ("Ver alimentación", "/feedlot/alimentacion", KIND_NAVIGATE, FIELD_MANAGERS, 50),
    ("Ver sanidad", "/feedlot/sanidad", KIND_NAVIGATE, FIELD_MANAGERS, 60),
    ("Ver pesajes", "/feedlot/pesajes", KIND_NAVIGATE, FIELD_MANAGERS, 70),
    ("Ver el mixer", "/feedlot/mixer", KIND_NAVIGATE, FIELD_MANAGERS, 80),
    ("Ver raciones", "/feedlot/racion", KIND_NAVIGATE, FIELD_MANAGERS, 90),
    ("Ver stocks", "/feedlot/stocks", KIND_NAVIGATE, FIELD_MANAGERS, 100),
    ("Ver cuenta corriente", "/feedlot/cuenta", KIND_NAVIGATE, FIELD_MANAGERS, 110),
    ("Ver gastos", "/feedlot/gastos", KIND_NAVIGATE, FIELD_MANAGERS, 120),
    ("Consultar al asesor", "/feedlot/asesor", KIND_NAVIGATE, FIELD_MANAGERS, 130),
)


class Command(BaseCommand):
    help = "Idempotently upserts the router starter menu into the Intent registry (#135)."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for phrase, target, kind, group_name, order in STARTER_MENU:
            group = None
            if group_name:
                group, _ = Group.objects.get_or_create(name=group_name)

            fields = {"target": target, "kind": kind, "group": group, "order": order}
            # `update_or_create` runs neither the path-relative validator nor the
            # reserved-outcome constraint; validate first so a bad starter row
            # fails here instead of landing in the registry. `validate_unique` is
            # off because the row being upserted already owns its phrase.
            Intent(phrase=phrase, **fields).full_clean(validate_unique=False)

            _row, created = Intent.objects.update_or_create(
                phrase=phrase,
                # `is_active` is absent on purpose: a re-run repairs where a
                # phrase points and who may see it, but never re-enables a row an
                # operator switched off in /admin/.
                defaults=fields,
                create_defaults={**fields, "is_active": True},
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            f"seed_router_menu: {created_count} created, {updated_count} updated, "
            f"{len(STARTER_MENU)} starter rows total"
        )
