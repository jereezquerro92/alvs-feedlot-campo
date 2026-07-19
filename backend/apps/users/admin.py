"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-10-auth]]
Docs: [[BACKEND]] · [[AUTH]]
LIVE-DOC:END"""

from django.contrib import admin

from apps.users.models import AccessRequest


ROLE_HELP_TEXT = (
    "Grant-only: saving a role mirrors it into the user's Django Groups and "
    "cannot be edited afterwards. Revoke or reassign by editing the user's "
    "Groups directly — clearing or changing this field never removes a Group "
    "(tdd-02: additive, never removing)."
)


@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at", "updated_at")
    list_filter = ("role",)
    readonly_fields = ("user", "created_at", "updated_at")

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.role_id is not None:
            return self.readonly_fields + ("role",)
        return self.readonly_fields

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "role" in form.base_fields:
            form.base_fields["role"].help_text = ROLE_HELP_TEXT
        return form
