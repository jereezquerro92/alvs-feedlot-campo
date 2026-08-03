"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Notification services — the only sanctioned write path for a Notification.

`build_weekly_digest` renders a client's own metrics to text (adr-36 decision 1);
it defines no metric — it reads `apps.metrics.services.summary`. `send_notification`
creates the immutable record and drives the channel sender, stamping the outcome
(adr-36 decisions 2–3). Nothing here touches the ledger (adr-36 decision 4).
"""

from datetime import timedelta

from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.metrics import services as metrics
from apps.notifications.models import Notification
from apps.notifications.senders import SenderError, get_sender


def _fmt_kg(value):
    if value is None:
        return "s/d"
    return f"{value:.0f} kg"


def _fmt_ars(value):
    if value is None:
        return "s/d"
    return f"$ {value:,.0f}".replace(",", ".")


def build_weekly_digest(*, client, end=None):
    """Render the last-7-days digest for one client as (subject, body).

    Reads `metrics.summary` for the [end-7, end] window; the numbers are the same
    the dashboard and the advisor read (adr-36 decision 1). Honest about missing
    data: a not-calculable conversion is stated as such, never a filler number.
    """
    end = end or timezone.localdate()
    start = end - timedelta(days=7)
    data = metrics.summary(client=client, start=start, end=end)

    herd = data["herd"]
    conv = data["conversion"]
    cost = data["cost"]

    if conv["conversion"] is None:
        conversion_line = "Conversión: no calculable esta semana"
    else:
        conversion_line = f"Conversión: {conv['conversion']:.2f} kg alimento / kg ganado"

    lines = [
        f"Hola {client.name}, tu resumen semanal ({start.isoformat()} a {end.isoformat()}):",
        "",
        f"Cabezas activas: {herd['head_count']}",
        f"Peso total: {_fmt_kg(herd['total_weight'])}",
        f"Peso promedio: {_fmt_kg(herd['average_weight'])}",
        conversion_line,
        f"Costo de la semana: {_fmt_ars(cost['total'])}",
        f"Saldo de cuenta: {_fmt_ars(data['balance'])}",
    ]
    subject = f"Resumen semanal — {client.name}"
    return subject, "\n".join(lines)


@transaction.atomic
def send_notification(*, client, channel, to_address, subject, body, created_by=None):
    """Create the record, drive the sender, stamp the outcome. Immutable after.

    A send failure is recorded on the row (status=failed, error) and never raised
    past this call — one client's failure must not stop a batch (adr-36 conseq.).
    """
    if not to_address:
        raise ValidationError("A destination address is required to notify.")

    notification = Notification.objects.create(
        client=client,
        channel=channel,
        to_address=to_address,
        subject=subject,
        body=body,
        status=Notification.Status.PENDING,
        created_by=created_by,
    )

    sender = get_sender(channel)
    try:
        provider_id = sender.send(to_address=to_address, subject=subject, body=body)
    except SenderError as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)[:255]
        notification.save(update_fields=["status", "error"])
        return notification

    notification.status = Notification.Status.SENT
    notification.provider_message_id = provider_id or ""
    notification.sent_at = timezone.now()
    notification.save(update_fields=["status", "provider_message_id", "sent_at"])
    return notification


def send_weekly_digest(*, client, channel, to_address, end=None, created_by=None):
    """Build this client's digest and send it — one record, one attempt."""
    subject, body = build_weekly_digest(client=client, end=end)
    return send_notification(
        client=client,
        channel=channel,
        to_address=to_address,
        subject=subject,
        body=body,
        created_by=created_by,
    )


asend_notification = sync_to_async(send_notification)
