"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import serializers

from apps.clients.models import Client
from apps.notifications.models import Notification
from apps.notifications.services import send_notification, build_weekly_digest


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "client", "channel", "to_address", "subject", "body",
            "status", "error", "provider_message_id",
            "created_at", "sent_at",
        ]
        read_only_fields = fields


class SendNotificationSerializer(serializers.Serializer):
    """Posting a notification builds the client's weekly digest and sends it through
    the service, so the record is created and the outcome stamped in one atomic step
    (adr-36 decisions 1–3)."""

    client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    channel = serializers.ChoiceField(choices=Notification.Channel.choices)
    to_address = serializers.CharField(max_length=200)

    def create(self, validated):
        request = self.context.get("request")
        created_by = getattr(request, "user", None)
        if created_by is not None and not created_by.is_authenticated:
            created_by = None
        subject, body = build_weekly_digest(client=validated["client"])
        notification = send_notification(
            client=validated["client"],
            channel=validated["channel"],
            to_address=validated["to_address"],
            subject=subject,
            body=body,
            created_by=created_by,
        )
        return NotificationSerializer(notification).data

    def to_representation(self, instance):
        return instance
