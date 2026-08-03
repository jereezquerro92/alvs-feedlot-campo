"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

from django.contrib import admin

from apps.clients.models import Account, Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "kind", "tax_id", "is_active", "created_at")
    list_filter = ("kind", "is_active")
    search_fields = ("name", "tax_id")


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("client", "balance_cached", "updated_at")
    readonly_fields = ("balance_cached", "updated_at")
