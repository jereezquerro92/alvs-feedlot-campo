"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]] · [[adr-03-api-and-backend]]
Docs: [[BACKEND]] · [[CHATBOT]]
API: [[API]]
LIVE-DOC:END"""

"""Models for the chatbot router choosing tier (adr-15-chatbot-two-tier).

Intent is the hand-authored menu registry: phrase, action target/kind, and
an optional group gate ([[GLOSSARY]] router registry model). IntentQuery is
the audit row persisted once per routed utterance ([[CHATBOT]] — Retention).
"""

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.validators import RegexValidator
from django.db import models

# Path-relative validator (adr-03/#107): Intent.target is a site-relative
# path such as "/dashboard/", never an absolute URL — pre-empts an intent
# row pointing off-site.
path_relative_validator = RegexValidator(
    regex=r"^/(?!/)[A-Za-z0-9\-_/]*$",
    message="target must be a path-relative string starting with '/' (no absolute URLs)",
)

KIND_NAVIGATE = "navigate"
KIND_CONFIRM = "confirm"
KIND_CHOICES = [
    (KIND_NAVIGATE, "navigate"),
    (KIND_CONFIRM, "confirm"),
]

# Reserved outcomes ([[GLOSSARY]]): always present, never registry rows.
NO_MATCH = "NO_MATCH"
ESCALATE = "ESCALATE"
RESERVED_OUTCOMES = (NO_MATCH, ESCALATE)


class Intent(models.Model):
    """A hand-authored menu row: phrase, action target, kind, group gate."""

    phrase = models.CharField(max_length=255, unique=True)
    target = models.CharField(max_length=255, validators=[path_relative_validator])
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, default=KIND_NAVIGATE)
    # Null/blank means ungated: visible to every authenticated user, including
    # a fresh Cognito user with no group membership (#103).
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL)
    # Explicit ordering column (#94) — Meta.ordering alone is not enough to
    # guarantee determinism across DB backends/migrations.
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(phrase__in=RESERVED_OUTCOMES),
                name="intent_phrase_not_reserved",
                violation_error_message="phrase must not be a reserved outcome (NO_MATCH, ESCALATE)",
            ),
        ]

    def __str__(self):
        return self.phrase


class IntentQuery(models.Model):
    """One audit row per routed utterance ([[CHATBOT]] — Retention).

    Retention (#65): the raw utterance is kept, but bounded by
    `ROUTER_AUDIT_RETENTION_DAYS` — `purge_router_audit` deletes rows older
    than that window by `created_at`. `chosen_intent` is `SET_NULL` on
    delete (#105): removing an `Intent` row must not cascade-delete, or be
    blocked by, its audit history. Field-level visibility of `utterance` /
    `raw_model_output` in Django admin is restricted to the "Router
    Auditors" group ([[CHATBOT]] — Retention).
    """

    utterance = models.TextField(null=True, blank=True)
    raw_model_output = models.TextField(null=True, blank=True)
    menu_offered = models.JSONField(default=list)
    choice = models.CharField(max_length=255)
    chosen_intent = models.ForeignKey(Intent, null=True, blank=True, on_delete=models.SET_NULL)
    model_id = models.CharField(max_length=255, blank=True)
    latency_ms = models.FloatField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "pk"]

    def __str__(self):
        return f"{self.user_id}:{self.choice}"
