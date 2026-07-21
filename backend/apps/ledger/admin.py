from django.contrib import admin

from apps.ledger.models import LedgerEntry, Payment


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "date", "direction", "amount", "concept", "source_kind")
    list_filter = ("direction", "concept")
    search_fields = ("description",)
    # Immutable ledger: entries are never edited from the admin (adr-25 rule 1).
    readonly_fields = tuple(f.name for f in LedgerEntry._meta.fields)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "date", "amount", "method", "reference")
    list_filter = ("method",)
