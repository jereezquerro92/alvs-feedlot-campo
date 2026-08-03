"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import mixins, viewsets

from apps.notifications.models import Notification
from apps.notifications.serializers import (
    NotificationSerializer,
    SendNotificationSerializer,
)
from apps.users.roles import NotificationsAccess


class NotificationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    """Outbound delivery records. list/retrieve/create; no update/destroy — a send
    record is immutable and a retry is a new notification (adr-36 decision 3)."""

    permission_classes = [NotificationsAccess]

    def get_serializer_class(self):
        if self.action == "create":
            return SendNotificationSerializer
        return NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.select_related("client")
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs
