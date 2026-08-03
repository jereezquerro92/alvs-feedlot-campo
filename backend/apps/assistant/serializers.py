"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import serializers

from apps.assistant.models import Conversation, Message
from apps.assistant.services import send_message
from apps.clients.models import Client


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id", "conversation", "role", "text",
            "input_snapshot", "model_id", "tokens", "latency_ms", "created_at",
        ]
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "client", "title", "created_at", "messages"]
        read_only_fields = ["id", "created_at", "messages"]


class SendMessageSerializer(serializers.Serializer):
    """Posting a turn goes through the service so the snapshot is backend-built and
    the assistant answer is generated in one atomic step (adr-35 decisions 2, 4)."""

    text = serializers.CharField()

    def create(self, validated):
        conversation = self.context["conversation"]
        request = self.context.get("request")
        created_by = getattr(request, "user", None)
        if created_by is not None and not created_by.is_authenticated:
            created_by = None
        answer = send_message(
            conversation=conversation, text=validated["text"], created_by=created_by
        )
        return MessageSerializer(answer).data

    def to_representation(self, instance):
        return instance
