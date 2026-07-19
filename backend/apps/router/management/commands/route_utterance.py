"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

"""`manage.py route_utterance --user <username> --utterance "<text>"`.

Terminal-first entry point for the chatbot router ([[CHATBOT]]). Uses
`get_inference_client`: the real Bedrock client in any non-DEBUG process,
the deterministic mock only under DEBUG (#253).
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.router.inference import get_inference_client
from apps.router.menu import build_menu
from apps.router.models import IntentQuery

User = get_user_model()


class Command(BaseCommand):
    help = "Route a free-text utterance for a user through the inference client (mock under DEBUG, Bedrock otherwise)."

    def add_arguments(self, parser):
        parser.add_argument("--user", required=True, help="username (sub) of the requesting user")
        parser.add_argument("--utterance", required=True, help="the free-text utterance to route")

    def handle(self, *args, **options):
        username = options["user"]
        utterance = options["utterance"]

        try:
            user = User.objects.get(**{User.USERNAME_FIELD: username})
        except User.DoesNotExist as exc:
            raise CommandError(f"no such user: {username}") from exc

        menu, _by_phrase = build_menu(user)
        client = get_inference_client()
        choice, latency_ms = client.choose(utterance, menu)

        audit_row = IntentQuery.objects.create(
            utterance=utterance,
            menu_offered=menu,
            choice=choice,
            model_id=client.model_id,
            latency_ms=latency_ms,
            user=user,
        )

        self.stdout.write(f"choice={choice} audit_row_id={audit_row.pk}")
