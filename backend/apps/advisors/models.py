"""AI advisors — the bounded generative capability (adr-27).

Three advisors (livestock, finance, admin) produce free analytical text over a
client's metrics. This is the one sanctioned exception to the router's
zero-generation posture (adr-15), fenced to this app: advisors are READ-ONLY over
data, reason only over a backend-assembled snapshot, and never act.

Every run is an AdvisorReport: snapshot in, text out, plus model_id/tokens/latency.
The report IS the record — reads return the stored report, generation is not
repeated. That is what makes an advisor's economic suggestion auditable: you can
see exactly what data it was shown.
"""

from django.conf import settings
from django.db import models


class Advisor(models.Model):
    """Catalog row, one per role. `system_prompt` is configuration, English-keyed."""

    class Slug(models.TextChoices):
        LIVESTOCK = "livestock", "Ganadero"
        FINANCE = "finance", "Contable-financiero"
        ADMIN = "admin", "Administrativo"

    slug = models.SlugField(max_length=20, unique=True, choices=Slug.choices)
    name = models.CharField(max_length=80)
    system_prompt = models.TextField(
        help_text="Rol base del asesor. Configuración, no código."
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.name


class AdvisorReport(models.Model):
    """One generation for one client and one period. Immutable once written."""

    advisor = models.ForeignKey(Advisor, on_delete=models.PROTECT, related_name="reports")
    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="advisor_reports")
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    # Exactly what the model was shown — the reproducibility anchor (adr-27 rule 3).
    input_snapshot = models.JSONField(default=dict)
    output = models.TextField(blank=True)

    # Inference audit (adr-27 rule 3).
    model_id = models.CharField(max_length=120, blank=True)
    tokens = models.PositiveIntegerField(null=True, blank=True)
    latency_ms = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["client", "advisor", "-created_at"])]

    def __str__(self):
        return f"{self.advisor_id} · client {self.client_id} · {self.created_at:%Y-%m-%d}"
