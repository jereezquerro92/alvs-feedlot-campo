"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Phase 9 (notifications): the outbound weekly digest and its delivery record (adr-36).

Read-only over domain data — sending posts no ledger entry and never mutates the
domain. The digest is rendered from `apps.metrics.summary` (one definition of each
number). Delivery runs against MockSender (DEBUG), never the network.
"""

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings

from apps.clients.models import Client
from apps.ledger.models import LedgerEntry
from apps.notifications.models import Notification
from apps.notifications.services import (
    build_weekly_digest,
    send_notification,
    send_weekly_digest,
)

pytestmark = pytest.mark.django_db

# DEBUG=True forces MockSender — delivery never hits the network (adr-36 decision 2),
# the same gate the advisors' and assistant's tests use for inference.
debug = override_settings(DEBUG=True)


def _client(name="Don Aldo", contact="+5493511234567"):
    return Client.objects.create(name=name, kind=Client.Kind.BOARDING, contact=contact)


def test_digest_renders_client_name_and_period():
    client = _client()
    subject, body = build_weekly_digest(client=client)
    assert client.name in subject
    assert client.name in body
    # An empty client has no measured growth — stated honestly, never a filler number.
    assert "no calculable" in body


@debug
def test_send_notification_marks_sent_and_stamps_provider_id():
    client = _client()
    notification = send_notification(
        client=client, channel=Notification.Channel.WHATSAPP,
        to_address=client.contact, subject="s", body="b",
    )
    assert notification.status == Notification.Status.SENT
    assert notification.provider_message_id.startswith("mock-whatsapp")
    assert notification.sent_at is not None


@debug
def test_send_notification_posts_no_ledger_entry():
    client = _client()
    send_notification(
        client=client, channel=Notification.Channel.WHATSAPP,
        to_address=client.contact, subject="s", body="b",
    )
    assert LedgerEntry.objects.filter(account=client.account).count() == 0


@debug
def test_send_weekly_digest_creates_one_immutable_record():
    client = _client()
    notification = send_weekly_digest(
        client=client, channel=Notification.Channel.WHATSAPP, to_address=client.contact
    )
    assert Notification.objects.count() == 1
    assert notification.status == Notification.Status.SENT
    assert client.name in notification.body


@debug
def test_missing_address_is_rejected_before_a_record_is_created():
    client = _client(contact="")
    with pytest.raises(ValidationError):
        send_notification(
            client=client, channel=Notification.Channel.WHATSAPP,
            to_address="", subject="s", body="b",
        )
    assert Notification.objects.count() == 0


def test_sender_failure_is_recorded_not_raised():
    # Outside DEBUG the real WhatsAppSender runs; with no credentials it raises
    # SenderError, which the service turns into a failed row (never propagated).
    client = _client()
    with override_settings(DEBUG=False, WHATSAPP_TOKEN="", WHATSAPP_PHONE_NUMBER_ID=""):
        notification = send_notification(
            client=client, channel=Notification.Channel.WHATSAPP,
            to_address=client.contact, subject="s", body="b",
        )
    assert notification.status == Notification.Status.FAILED
    assert notification.error
    assert notification.sent_at is None


@debug
def test_a_retry_is_a_new_record_not_an_edit():
    client = _client()
    first = send_weekly_digest(
        client=client, channel=Notification.Channel.WHATSAPP, to_address=client.contact
    )
    second = send_weekly_digest(
        client=client, channel=Notification.Channel.WHATSAPP, to_address=client.contact
    )
    assert first.pk != second.pk
    assert Notification.objects.count() == 2
