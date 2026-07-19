"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

"""`manage.py seed_demo_operator` — test/dev-scope seed of one demo Operator.

Creates (idempotently) a single demo user in the `ai_operators` group so a
local/dev environment can exercise the RBAC gate without manual `/admin/`
setup. This never touches the bootstrap superuser exception
([[adr-10-auth]] rule 8) and never seeds a real human account — Operator
onboarding for real users stays manual group assignment in `/admin/`.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from apps.router.permissions import AI_OPERATORS_GROUP

DEMO_OPERATOR_SUB = "demo-operator"

User = get_user_model()


class Command(BaseCommand):
    help = "Idempotently seeds one demo Operator user in the ai_operators group (test/dev scope)."

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name=AI_OPERATORS_GROUP)
        user, _ = User.objects.get_or_create(
            sub=DEMO_OPERATOR_SUB,
            defaults={"email": "demo-operator@example.com"},
        )
        user.groups.add(group)
        self.stdout.write(f"seed_demo_operator: user sub={user.sub} in group={AI_OPERATORS_GROUP}")
