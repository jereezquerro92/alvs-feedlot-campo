"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Phase 8 (assistant): the conversational generating tier (adr-35).

Read-only over domain data — a turn writes only its own Message rows, never a
ledger entry, never a domain mutation. Every assistant turn is generated over a
backend-built, per-client snapshot and persisted with its inference audit.
Inference runs against MockAssistantClient (DEBUG), never the network.
"""

from decimal import Decimal

import pytest
from django.test import override_settings

from apps.assistant.models import Conversation, Message
from apps.assistant.services import send_message
from apps.clients.models import Client
from apps.ledger.models import LedgerEntry

pytestmark = pytest.mark.django_db

# DEBUG=True forces MockAssistantClient — inference never hits the network
# (adr-35 decision 5), the same gate the advisors' tests use.
debug = override_settings(DEBUG=True)


def _conversation():
    client = Client.objects.create(name="Don Aldo", kind=Client.Kind.BOARDING)
    return Conversation.objects.create(client=client, title="Consulta")


@debug
def test_send_message_persists_user_then_assistant_turn():
    conversation = _conversation()
    answer = send_message(conversation=conversation, text="¿Cuántas cabezas tengo?")

    turns = list(conversation.messages.all())
    assert [t.role for t in turns] == [Message.Role.USER, Message.Role.ASSISTANT]
    assert turns[0].text == "¿Cuántas cabezas tengo?"
    assert answer.role == Message.Role.ASSISTANT
    assert answer.text  # the mock produced grounded text


@debug
def test_assistant_turn_is_audited_with_snapshot_and_model():
    conversation = _conversation()
    answer = send_message(conversation=conversation, text="hola")

    assert answer.model_id == "mock-assistant-double"
    assert "herd" in answer.input_snapshot
    assert answer.input_snapshot["client"]["id"] == conversation.client_id


@debug
def test_send_message_posts_no_ledger_entry():
    conversation = _conversation()
    send_message(conversation=conversation, text="¿cuánto debo?")
    assert LedgerEntry.objects.filter(account=conversation.client.account).count() == 0


@debug
def test_snapshot_is_scoped_to_the_conversation_client():
    other = Client.objects.create(name="Otro", kind=Client.Kind.BOARDING)
    conversation = _conversation()
    answer = send_message(conversation=conversation, text="dame mis datos")
    # The snapshot only ever names this conversation's client, never another's.
    assert answer.input_snapshot["client"]["id"] == conversation.client_id
    assert answer.input_snapshot["client"]["id"] != other.id


@debug
def test_history_grows_across_turns():
    conversation = _conversation()
    send_message(conversation=conversation, text="primera")
    send_message(conversation=conversation, text="segunda")
    roles = list(conversation.messages.values_list("role", flat=True))
    assert roles == ["user", "assistant", "user", "assistant"]


@debug
def test_reading_a_message_does_not_reinfer():
    conversation = _conversation()
    answer = send_message(conversation=conversation, text="una sola vez")
    before = answer.text
    fetched = Message.objects.get(pk=answer.pk)
    assert fetched.text == before
    # Still exactly two turns — no generation on read.
    assert conversation.messages.count() == 2


@debug
def test_snapshot_carries_a_json_safe_balance():
    conversation = _conversation()
    # a Decimal balance must be stringified into the stored snapshot (JSON-safe)
    conversation.client.account.balance_cached = Decimal("1234.50")
    conversation.client.account.save()
    answer = send_message(conversation=conversation, text="saldo?")
    assert isinstance(answer.input_snapshot["balance"], str)
