"""Conversational assistant — the generating tier of adr-15, bounded (adr-35).

The assistant produces free analytical text over ONE client's metrics and is
READ-ONLY forever: it never acts, never posts a ledger entry, never flips a switch
(adr-15 rule 1, adr-35 decision 1). It is the multi-turn counterpart of the
advisors (adr-27): a `Conversation` is a per-client thread, and every `Message` of
role `assistant` carries the snapshot it saw plus its inference audit — the record
that makes each answer reproducible (adr-35 decision 4).
"""

from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """A per-client Q&A thread. Scope is a hard boundary (adr-35 decision 2)."""

    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="conversations"
    )
    title = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["client", "-created_at"])]

    def __str__(self):
        return f"conversation {self.id} · client {self.client_id}"


class Message(models.Model):
    """One turn in a conversation. Immutable once written (adr-35 decision 6)."""

    class Role(models.TextChoices):
        USER = "user", "Usuario"
        ASSISTANT = "assistant", "Asistente"

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    text = models.TextField()

    # Audit for assistant turns — exactly what the model was shown (adr-35 decision 4).
    input_snapshot = models.JSONField(default=dict, blank=True)
    model_id = models.CharField(max_length=120, blank=True)
    tokens = models.PositiveIntegerField(null=True, blank=True)
    latency_ms = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["conversation", "created_at"])]

    def __str__(self):
        return f"{self.role} · conversation {self.conversation_id}"
