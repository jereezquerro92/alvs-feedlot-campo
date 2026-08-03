"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Delivery senders (adr-36 decision 2), mirroring the inference clients' gate.

`get_sender(channel)` is the one selection point: DEBUG → `MockSender` (network-free,
records what it "sent"); deploy → the real sender for the channel. No setting forces
the mock into a deploy — the exact gate the advisors and assistant use.
"""

from django.conf import settings


class SenderError(Exception):
    """Raised when a real send fails — the service turns it into a failed row."""


class MockSender:
    """Deterministic test double. Never hits the network; returns a fake id."""

    def __init__(self, channel):
        self.channel = channel
        self.sent = []

    def send(self, *, to_address, subject, body):
        self.sent.append({"to": to_address, "subject": subject, "body": body})
        return f"mock-{self.channel}-{len(self.sent)}"


class WhatsAppSender:
    """Real WhatsApp Cloud API sender. Credentials are deferred (adr-36 conseq.).

    Reads `WHATSAPP_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` at call time; a missing
    credential is a `SenderError`, never a silent no-op. Never constructed in DEBUG.
    """

    channel = "whatsapp"

    def send(self, *, to_address, subject, body):
        import json
        import urllib.error
        import urllib.request

        token = getattr(settings, "WHATSAPP_TOKEN", "")
        phone_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")
        if not token or not phone_id:
            raise SenderError("WhatsApp credentials are not configured.")

        text = f"*{subject}*\n\n{body}" if subject else body
        payload = json.dumps(
            {
                "messaging_product": "whatsapp",
                "to": to_address,
                "type": "text",
                "text": {"body": text},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"https://graph.facebook.com/v20.0/{phone_id}/messages",
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:  # network / HTTP error
            raise SenderError(str(exc)) from exc
        try:
            return data["messages"][0]["id"]
        except (KeyError, IndexError, TypeError):
            return ""


def get_sender(channel):
    """DEBUG → mock; deploy → the real sender for the channel."""
    if settings.DEBUG:
        return MockSender(channel)
    if channel == "whatsapp":
        return WhatsAppSender()
    raise SenderError(f"No real sender for channel '{channel}'.")
