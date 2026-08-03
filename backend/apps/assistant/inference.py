"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Assistant inference clients (adr-35 decision 5), mirroring the advisors' pair.

`AssistantBedrockClient` is the real generative client: a Bedrock `converse` call
carrying the conversation history plus the client snapshot, returning free text.
Temperature is 0.3 — this tier generates prose, unlike the router's pinned 0. It
stays READ-ONLY and never acts (adr-15 rule 1).

`MockAssistantClient` is the DEBUG-only deterministic stand-in that never hits the
network. `get_assistant_client` gates it exactly like the router and the advisors:
a non-DEBUG process can only ever construct the real client — no setting forces the
mock into a deploy (adr-35 decision 5).
"""

import json
import time

from django.conf import settings

MOCK_MODEL_ID = "mock-assistant-double"

SYSTEM_PROMPT = (
    "Sos un asistente que responde preguntas sobre los datos de UN cliente de un "
    "feedlot. Respondé en español, solo con lo que está en el snapshot y el "
    "historial. No inventes datos que no estén; si un número no se puede calcular, "
    "decílo. No ejecutás acciones: solo informás."
)


class AssistantBedrockClient:
    """Real generative client. Returns (text, model_id, tokens, latency_ms)."""

    def __init__(self, model_id=None, region=None):
        import boto3

        self.model_id = model_id or getattr(settings, "ASSISTANT_BEDROCK_MODEL_ID", None)
        self._client = boto3.client(
            "bedrock-runtime", region_name=region or getattr(settings, "BEDROCK_REGION", None)
        )

    def generate(self, *, snapshot, history, question):
        messages = []
        for turn in history:
            messages.append(
                {"role": turn["role"], "content": [{"text": turn["text"]}]}
            )
        grounded = (
            "Datos del cliente (snapshot):\n"
            f"{json.dumps(snapshot, ensure_ascii=False, indent=2)}\n\n"
            f"Pregunta: {question}"
        )
        messages.append({"role": "user", "content": [{"text": grounded}]})

        started = time.monotonic()
        response = self._client.converse(
            modelId=self.model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            inferenceConfig={"temperature": 0.3, "maxTokens": 1000},
        )
        latency_ms = (time.monotonic() - started) * 1000.0
        try:
            text = response["output"]["message"]["content"][0]["text"].strip()
        except (KeyError, IndexError, TypeError, AttributeError):
            text = ""
        tokens = None
        try:
            tokens = response.get("usage", {}).get("totalTokens")
        except AttributeError:
            pass
        return text, self.model_id, tokens, latency_ms


class MockAssistantClient:
    """Deterministic test double: a short, data-grounded answer. Network-free."""

    model_id = MOCK_MODEL_ID

    def generate(self, *, snapshot, history, question):
        herd = snapshot.get("herd", {})
        balance = snapshot.get("balance")
        text = (
            f"[respuesta determinista] Sobre «{question}»: "
            f"cabezas {herd.get('head_count')}, saldo {balance}, "
            f"conversión {snapshot.get('conversion', {}).get('conversion')}."
        )
        return text, self.model_id, 0, 0.0


def get_assistant_client():
    """One selection point. DEBUG → mock; deploy → real Bedrock. No override."""
    if settings.DEBUG:
        return MockAssistantClient()
    return AssistantBedrockClient()
