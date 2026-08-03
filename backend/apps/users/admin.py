"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]] · [[adr-44-field-operational-roles]] · [[adr-20-authorization-lobby]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

from django.contrib import admin

from apps.users.models import AccessRequest


ROLE_HELP_TEXT = (
    "Set-sync: saving this field strips every ROLE_GROUPS membership that is "
    "not the chosen role, then adds the chosen Group when set. Clear to null "
    "to remove all matrix role Groups; admins/ai_operators and other "
    "out-of-matrix Groups are left alone (tdd-02 / adr-20 rule 3)."
)


CLIENT_HELP_TEXT = (
    "Only for a lot_owners session: the single Client this user's portal is "
    "confined to (adr-44). A lot_owners user with no client bound sees nothing "
    "(fails closed). Ignored for every other role."
)


@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "client", "created_at", "updated_at")
    list_filter = ("role",)
    readonly_fields = ("user", "created_at", "updated_at")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "role" in form.base_fields:
            form.base_fields["role"].help_text = ROLE_HELP_TEXT
        if "client" in form.base_fields:
            form.base_fields["client"].help_text = CLIENT_HELP_TEXT
        return form
