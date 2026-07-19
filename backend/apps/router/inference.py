"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

"""Inference clients for the chatbot router choosing tier.

`BedrockInferenceClient` is the real client: a `boto3` `bedrock-runtime`
`converse` call at temperature 0 whose only sanctioned output is one verbatim
member of the closed menu ([[adr-15-chatbot-two-tier]] rule 7); anything else
is hard-rejected by the caller, never repaired. It is synchronous by design —
callers on the event loop wrap it in `asgiref.sync_to_async`, never
`aiobotocore` ([[adr-16-async-mandatory]] rule 4).

`MockInferenceClient` is the DEBUG-only deterministic stand-in: it never hits
the network and always returns a menu member. `get_inference_client` gates it
exactly as the dev-auth path is gated ([[adr-10-auth]] rule 6 precedent):
`DEBUG=False` can never reach the mock.
"""

import time

from django.conf import settings

MOCK_MODEL_ID = "mock-inference-double"

_SYSTEM_PROMPT = (
    "You are a routing classifier. You are given a numbered menu of phrases "
    "and a user utterance. Reply with exactly one phrase from the menu, "
    "copied verbatim, and nothing else — no numbering, no punctuation, no "
    "explanation. Never invent a phrase that is not in the menu."
)


class BedrockInferenceClient:
    """Real choosing-tier client: Bedrock `converse`, temperature 0.

    The closed-enum guarantee does NOT live here: this client returns the
    model's raw text and the caller enforces menu membership with a hard
    reject ([[adr-15-chatbot-two-tier]] rule 2). An empty or malformed model
    response is returned as "" — never a menu member, so it always rejects.
    """

    def __init__(self, model_id=None, region=None):
        import boto3

        self.model_id = model_id or settings.ROUTER_BEDROCK_MODEL_ID
        self._client = boto3.client(
            "bedrock-runtime", region_name=region or settings.BEDROCK_REGION
        )

    def choose(self, utterance, menu):
        """Return (choice_text, latency_ms). Raises on transport/IAM/model
        failure — the caller owns degrading the router surface, not this
        client. Menu is never empty (build_menu appends the reserved
        outcomes)."""
        menu_lines = "\n".join(f"- {entry['phrase']}" for entry in menu)
        prompt = f"Menu:\n{menu_lines}\n\nUtterance: {utterance}"
        started = time.monotonic()
        response = self._client.converse(
            modelId=self.model_id,
            system=[{"text": _SYSTEM_PROMPT}],
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0.0, "maxTokens": 100},
        )
        latency_ms = (time.monotonic() - started) * 1000.0
        try:
            choice = response["output"]["message"]["content"][0]["text"].strip()
        except (KeyError, IndexError, TypeError, AttributeError):
            choice = ""
        return choice, latency_ms


def get_inference_client():
    """The one selection point between mock and real inference.

    Mirrors [[adr-10-auth]] rule 6: the mock is a DEBUG-only development
    path; a non-DEBUG process can only ever construct the real Bedrock
    client. No setting can force the mock into a deploy context.
    """
    if settings.DEBUG:
        return MockInferenceClient()
    return BedrockInferenceClient()


class MockInferenceClient:
    """Deterministic test double: always picks the first menu entry."""

    model_id = MOCK_MODEL_ID

    def choose(self, utterance, menu):
        """Return (choice_phrase, latency_ms) for `utterance` given `menu`.

        Deterministic and network-free: picks the first entry in the
        supplied menu. `menu` is never empty — build_menu always appends the
        two reserved outcomes (#104).
        """
        chosen = menu[0]["phrase"]
        return chosen, 0.0
