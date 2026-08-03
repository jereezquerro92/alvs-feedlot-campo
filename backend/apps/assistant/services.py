"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Assistant conversation flow (adr-35).

`send_message` is the whole turn: persist the user's message, assemble the
client-scoped snapshot (built here, never passed in, so a caller can never smuggle
another client's data — adr-35 decision 2), run inference over the thread history +
snapshot, persist the assistant's answer as its own auditable record.

Read-only over domain data (adr-35 decision 1): the only rows this writes are the
conversation's own `Message`s. It never posts a ledger entry and never acts.
"""

from asgiref.sync import sync_to_async
from django.db import transaction

from apps.advisors.snapshot import build_snapshot
from apps.assistant.inference import get_assistant_client
from apps.assistant.models import Conversation, Message


def _history(conversation):
    """Prior turns as inference-shaped dicts, in chronological order."""
    return [
        {"role": m.role, "text": m.text}
        for m in conversation.messages.all()
    ]


@transaction.atomic
def send_message(*, conversation: Conversation, text: str, created_by=None):
    """Post a user turn and generate the assistant's grounded answer.

    Returns the assistant `Message`. The snapshot is built from the conversation's
    own client — the per-client scope is a hard boundary, not a convention.

    Prior turns are snapshotted *before* the new user row is persisted so Bedrock
    history never ends in a user turn that `generate` then duplicates (#13 / #60).
    """
    # Prior alternating turns only — not the question we are about to persist.
    history = _history(conversation)
    Message.objects.create(
        conversation=conversation, role=Message.Role.USER, text=text
    )

    snapshot = build_snapshot(client=conversation.client)

    client_inference = get_assistant_client()
    answer, model_id, tokens, latency_ms = client_inference.generate(
        snapshot=snapshot, history=history, question=text
    )
    if not (answer or "").strip():
        # Never persist a blank answer as a successful turn (#25 / #60).
        raise RuntimeError("assistant_unavailable")

    return Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        text=answer,
        input_snapshot=snapshot,
        model_id=model_id,
        tokens=tokens,
        latency_ms=latency_ms,
    )


# Async entrypoint for event-loop callers (adr-16 rule 4): the Bedrock inference
# inside `send_message` is a blocking boto3 `converse`, so a future streaming/SSE
# assistant view awaits it through `sync_to_async`, never `aiobotocore`. The sync
# view keeps calling `send_message` directly (adr-16 rule 1: sync `def` is default).
asend_message = sync_to_async(send_message)
