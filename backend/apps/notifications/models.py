"""Outbound notifications — the weekly digest and its delivery record (adr-36).

`notifications` is READ-ONLY over domain data (adr-36 decision 4): it reads a
client's metrics, renders a digest, and sends it. It posts no ledger entry and
never acts on the domain. A `Notification` is an immutable record of one send
attempt — its `status` is written once by the service, never hand-edited.
"""

from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Channel(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "Email"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        SENT = "sent", "Enviada"
        FAILED = "failed", "Fallida"

    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="notifications"
    )
    channel = models.CharField(max_length=10, choices=Channel.choices)
    to_address = models.CharField(max_length=200)
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    error = models.CharField(max_length=255, blank=True)
    provider_message_id = models.CharField(max_length=120, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["client", "-created_at"])]

    def __str__(self):
        return f"{self.channel} → {self.to_address} ({self.status})"
