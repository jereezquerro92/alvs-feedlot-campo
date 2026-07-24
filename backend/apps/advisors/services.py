"""Advisor report generation (adr-27).

`generate_report` is the whole flow: assemble the client-scoped snapshot, run
inference, persist an AdvisorReport. The snapshot is built here, not passed in, so
a caller can never smuggle in another client's data — the per-client scope is a
hard boundary (adr-27 rule 2).
"""

from asgiref.sync import sync_to_async
from django.db import transaction

from apps.advisors.inference import get_advisor_client
from apps.advisors.models import Advisor, AdvisorReport
from apps.advisors.snapshot import build_snapshot


@transaction.atomic
def generate_report(*, advisor: Advisor, client, start=None, end=None, created_by=None):
    if not advisor.is_active:
        from django.core.exceptions import ValidationError

        raise ValidationError(f"El asesor {advisor.slug} está inactivo.")

    snapshot = build_snapshot(client=client, start=start, end=end)

    client_inference = get_advisor_client()
    text, model_id, tokens, latency_ms = client_inference.generate(
        system_prompt=advisor.system_prompt, snapshot=snapshot
    )

    return AdvisorReport.objects.create(
        advisor=advisor,
        client=client,
        period_start=start,
        period_end=end,
        input_snapshot=snapshot,
        output=text,
        model_id=model_id,
        tokens=tokens,
        latency_ms=latency_ms,
        created_by=created_by,
    )


# Async entrypoint for event-loop callers (adr-16 rule 4): the Bedrock inference
# inside `generate_report` is a blocking boto3 `converse`, so an `async def` view
# — a future streaming/SSE advisor endpoint — awaits it through `sync_to_async`,
# never `aiobotocore`. The sync view keeps calling `generate_report` directly:
# a plain `def` view is the unchanged default (adr-16 rule 1).
agenerate_report = sync_to_async(generate_report)
