"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

"""`manage.py check_bedrock_connectivity` — the blocking Bedrock gate (#253).

Proves the REAL inference path end to end: network, IAM grant, and model
access on `ROUTER_BEDROCK_MODEL_ID` in `BEDROCK_REGION`, via the cheapest
real call (single `converse`, maxTokens=1). It always constructs
`BedrockInferenceClient` directly — never the mock, regardless of DEBUG.
Hard-fails (non-zero exit) on any failure; it is never a warning.

Runs from a developer terminal and as the deploy-pipeline gate step
(`pytest -m bedrock_live` wraps it in CI) — never at prod container boot:
a Bedrock outage degrades the router surface only ([[CHATBOT]]).
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.router.inference import BedrockInferenceClient


class Command(BaseCommand):
    help = "Blocking gate: prove real Bedrock connectivity (network + IAM + model access) or exit non-zero."

    def handle(self, *args, **options):
        client = BedrockInferenceClient()
        try:
            response = client._client.converse(
                modelId=client.model_id,
                messages=[{"role": "user", "content": [{"text": "ping"}]}],
                inferenceConfig={"temperature": 0.0, "maxTokens": 1},
            )
        except Exception as exc:
            raise CommandError(
                f"Bedrock connectivity FAILED for model {client.model_id} "
                f"in {settings.BEDROCK_REGION}: {exc}"
            ) from exc

        latency = response.get("metrics", {}).get("latencyMs")
        self.stdout.write(
            f"ok  bedrock reachable: model={client.model_id} "
            f"region={settings.BEDROCK_REGION} latency_ms={latency}"
        )
