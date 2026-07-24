"""Advisor inference clients (adr-27 rule 4), mirroring apps.router.inference.

`AdvisorBedrockClient` is the real generative client: a Bedrock `converse` call
that returns free analytical text — the bounded generative exception (adr-27
rule 1). Unlike the router's choosing tier, temperature is not pinned to 0: this
tier generates prose. It stays read-only and never acts.

`MockAdvisorClient` is the DEBUG-only deterministic stand-in that never hits the
network. `get_advisor_client` gates it exactly like the router does: a non-DEBUG
process can only ever construct the real client — no setting forces the mock into
a deploy.

INTEGRATION POINT (Claude Code, against live AWS): confirm BEDROCK model id and
region settings, IAM, and the async wrapping (adr-16) before relying on the real
client in production.
"""

import json
import time

from django.conf import settings

MOCK_MODEL_ID = "mock-advisor-double"


class AdvisorBedrockClient:
    """Real generative client. Returns (text, model_id, tokens, latency_ms).

    Raises on transport/IAM/model failure — the caller owns degrading the surface,
    not this client.
    """

    def __init__(self, model_id=None, region=None):
        import boto3

        self.model_id = model_id or getattr(settings, "ADVISOR_BEDROCK_MODEL_ID", None)
        self._client = boto3.client(
            "bedrock-runtime", region_name=region or getattr(settings, "BEDROCK_REGION", None)
        )

    def generate(self, *, system_prompt, snapshot):
        prompt = (
            "Analizá los siguientes datos de UN cliente y período. Respondé en "
            "español, con recomendaciones concretas y señalando su margen de error. "
            "No inventes datos que no estén acá.\n\n"
            f"{json.dumps(snapshot, ensure_ascii=False, indent=2)}"
        )
        started = time.monotonic()
        response = self._client.converse(
            modelId=self.model_id,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0.3, "maxTokens": 1200},
        )
        latency_ms = (time.monotonic() - started) * 1000.0
        try:
            text = response["output"]["message"]["content"][0]["text"].strip()
        except (KeyError, IndexError, TypeError, AttributeError):
            text = ""
        tokens = None
        try:
            usage = response.get("usage", {})
            tokens = usage.get("totalTokens")
        except AttributeError:
            pass
        return text, self.model_id, tokens, latency_ms


class MockAdvisorClient:
    """Deterministic test double: echoes a short, data-grounded summary.

    Network-free. Produces text that references real numbers from the snapshot so
    tests can assert the advisor saw the data, without asserting model prose.
    """

    model_id = MOCK_MODEL_ID

    def generate(self, *, system_prompt, snapshot):
        herd = snapshot.get("herd", {})
        balance = snapshot.get("balance")
        text = (
            f"[resumen determinista] Cabezas: {herd.get('head_count')}. "
            f"Saldo: {balance}. "
            f"Conversión: {snapshot.get('conversion', {}).get('conversion')}."
        )
        return text, self.model_id, 0, 0.0


def get_advisor_client():
    """One selection point. DEBUG → mock; deploy → real Bedrock. No override."""
    if settings.DEBUG:
        return MockAdvisorClient()
    return AdvisorBedrockClient()
