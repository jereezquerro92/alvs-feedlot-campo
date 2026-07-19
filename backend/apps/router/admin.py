"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

"""Admin registration for the router app ([[CHATBOT]] — Retention, #65).

`utterance` and `raw_model_output` on `IntentQuery` carry the raw user
utterance / raw model response — visible in Django admin only to members of
the "Router Auditors" group. Every other admin user sees the row with those
two fields excluded, not merely blanked.
"""

from django.contrib import admin

from apps.router.models import Intent, IntentQuery

ROUTER_AUDITORS_GROUP = "Router Auditors"
RESTRICTED_FIELDS = ("utterance", "raw_model_output")


@admin.register(Intent)
class IntentAdmin(admin.ModelAdmin):
    list_display = ("phrase", "target", "kind", "group", "order", "is_active")


@admin.register(IntentQuery)
class IntentQueryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "choice", "chosen_intent", "model_id", "created_at")
    readonly_fields = ("created_at",)

    def _user_is_router_auditor(self, request):
        user = request.user
        return user.is_superuser or user.groups.filter(name=ROUTER_AUDITORS_GROUP).exists()

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if self._user_is_router_auditor(request):
            return fields
        return [f for f in fields if f not in RESTRICTED_FIELDS]

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if self._user_is_router_auditor(request):
            return list_display
        return tuple(f for f in list_display if f not in RESTRICTED_FIELDS)
