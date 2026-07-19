"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.router.inference import MockInferenceClient
from apps.router.models import IntentQuery

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_route_utterance_returns_menu_choice_via_stub_with_zero_network_calls():
    User.objects.create_user(sub="sub-plain")

    with (
        patch(
            "apps.router.management.commands.route_utterance.get_inference_client",
            MockInferenceClient,
        ),
        patch(
            "apps.router.inference.MockInferenceClient.choose",
            wraps=MockInferenceClient().choose,
        ) as spy,
    ):
        call_command("route_utterance", user="sub-plain", utterance="hi")

    assert spy.call_count == 1
    assert IntentQuery.objects.count() == 1
    row = IntentQuery.objects.get()
    assert row.utterance == "hi"
    assert row.choice
    assert row.model_id == MockInferenceClient.model_id


def test_route_utterance_no_boto3_or_network_import():
    """Importing the inference module must not pull boto3 into sys.modules —
    only constructing `BedrockInferenceClient` does (lazy import), so the
    mock path stays entirely network-free ([[adr-16-async-mandatory]])."""
    import sys

    import apps.router.inference as inference_module

    assert "boto3" not in dir(inference_module)
    assert "boto3" not in sys.modules


def test_route_utterance_unknown_user_raises_command_error():
    with pytest.raises(CommandError):
        call_command("route_utterance", user="does-not-exist", utterance="hi")
