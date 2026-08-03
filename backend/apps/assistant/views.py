"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.assistant.models import Conversation, Message
from apps.assistant.serializers import (
    ConversationSerializer,
    MessageSerializer,
    SendMessageSerializer,
)
from apps.users.roles import (
    AssistantAccess,
    bound_client_id,
    is_assistant_portal_session,
)


class ConversationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    """Per-client Q&A threads. list/retrieve/create; no update/destroy — a turn is
    corrected by another turn, never edited (adr-35 decision 6)."""

    permission_classes = [AssistantAccess]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        qs = Conversation.objects.prefetch_related("messages").select_related("client")
        # A lot-owner portal session sees ONLY its bound client's threads, whatever
        # ``?client=`` says; an unbound one sees none — fail closed (adr-44 dec 3-4).
        if is_assistant_portal_session(self.request.user):
            bound = bound_client_id(self.request.user)
            return qs.filter(client_id=bound) if bound is not None else qs.none()
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs

    def perform_create(self, serializer):
        user = getattr(self.request, "user", None)
        if user is not None and not user.is_authenticated:
            user = None
        # A portal session's thread is pinned to its bound client, never the body
        # value — belt-and-suspenders behind AssistantAccess.has_permission.
        if is_assistant_portal_session(self.request.user):
            serializer.save(created_by=user, client_id=bound_client_id(self.request.user))
        else:
            serializer.save(created_by=user)

    @action(detail=True, methods=["get", "post"])
    def messages(self, request, pk=None):
        """GET lists the thread's turns; POST sends a user turn and returns the
        assistant's grounded answer, generated over a backend-built snapshot
        (adr-35 decisions 2, 4)."""
        conversation = self.get_object()
        if request.method == "GET":
            data = MessageSerializer(conversation.messages.all(), many=True).data
            return Response(data)

        serializer = SendMessageSerializer(
            data=request.data,
            context={"conversation": conversation, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=201)
