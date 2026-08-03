"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

from django.contrib import admin

from apps.expenses.models import ExpenseEvent


@admin.register(ExpenseEvent)
class ExpenseEventAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "client", "lot", "title", "category", "total_cost")
    list_filter = ("date", "category")
    search_fields = ("title", "fuel_kind")
    readonly_fields = ("created_at",)
