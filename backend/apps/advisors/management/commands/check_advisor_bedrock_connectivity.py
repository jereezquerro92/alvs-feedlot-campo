"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-16-async-mandatory]] · [[adr-27-advisors-generative]]
Docs: [[BACKEND]] · [[FEEDLOT]]
LIVE-DOC:END"""

"""`manage.py check_advisor_bedrock_connectivity` — the blocking advisor gate.

The advisors' twin of the router's `check_bedrock_connectivity` (adr-31 pending
integration point). Proves the REAL generative path end to end: network, IAM grant,
and model access on `ADVISOR_BEDROCK_MODEL_ID` in `BEDROCK_REGION`, via the cheapest
real call (single `converse`, maxTokens=1). It always constructs
`AdvisorBedrockClient` directly — never the mock, regardless of DEBUG.
Hard-fails (non-zero exit) on any failure; it is never a warning.

Runs from a developer terminal and as the deploy-pipeline gate step
(`pytest -m bedrock_live` wraps it in CI) — never at prod container boot: a Bedrock
outage degrades the advisor surface only, it must not stop the app booting.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.advisors.inference import AdvisorBedrockClient


class Command(BaseCommand):
    help = "Blocking gate: prove real advisor Bedrock connectivity (network + IAM + model access) or exit non-zero."

    def handle(self, *args, **options):
        client = AdvisorBedrockClient()
        try:
            response = client._client.converse(
                modelId=client.model_id,
                messages=[{"role": "user", "content": [{"text": "ping"}]}],
                inferenceConfig={"temperature": 0.0, "maxTokens": 1},
            )
        except Exception as exc:
            raise CommandError(
                f"Advisor Bedrock connectivity FAILED for model {client.model_id} "
                f"in {settings.BEDROCK_REGION}: {exc}"
            ) from exc

        latency = response.get("metrics", {}).get("latencyMs")
        self.stdout.write(
            f"ok  advisor bedrock reachable: model={client.model_id} "
            f"region={settings.BEDROCK_REGION} latency_ms={latency}"
        )
