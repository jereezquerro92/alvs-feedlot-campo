"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

"""Tests for the inference clients and their selection (#253):
`get_inference_client` gating (mock is DEBUG-only, [[adr-10-auth]] rule 6
precedent), `BedrockInferenceClient.choose` request shape (temperature 0,
[[adr-15-chatbot-two-tier]] rule 7), and its raw-output contract — the
closed-enum guarantee stays in the caller, never here."""

import pytest

from apps.router.inference import (
    BedrockInferenceClient,
    MockInferenceClient,
    get_inference_client,
)

MENU = [{"phrase": "log out"}, {"phrase": "NO_MATCH"}, {"phrase": "ESCALATE"}]


class _FakeBedrockRuntime:
    """Stands in for the boto3 bedrock-runtime client — records the converse
    kwargs and returns a canned response. No boto3 import, no network."""

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


def _client(fake):
    client = BedrockInferenceClient.__new__(BedrockInferenceClient)
    client.model_id = "test-model"
    client._client = fake
    return client


def _response(text):
    return {"output": {"message": {"content": [{"text": text}]}}}


def test_factory_returns_mock_only_under_debug(settings, monkeypatch):
    settings.DEBUG = True
    assert isinstance(get_inference_client(), MockInferenceClient)

    settings.DEBUG = False
    monkeypatch.setattr(BedrockInferenceClient, "__init__", lambda self: None)
    assert isinstance(get_inference_client(), BedrockInferenceClient)


def test_choose_sends_temperature_zero_and_full_menu():
    fake = _FakeBedrockRuntime(response=_response("log out"))
    choice, latency_ms = _client(fake).choose("log me out", MENU)

    assert choice == "log out"
    assert latency_ms >= 0
    (call,) = fake.calls
    assert call["modelId"] == "test-model"
    assert call["inferenceConfig"]["temperature"] == 0.0
    prompt = call["messages"][0]["content"][0]["text"]
    for entry in MENU:
        assert entry["phrase"] in prompt
    assert "log me out" in prompt


def test_choose_returns_raw_text_even_off_menu():
    """The client never repairs or nearest-matches — the hard reject lives
    in the view ([[adr-15-chatbot-two-tier]] rule 2)."""
    fake = _FakeBedrockRuntime(response=_response("something invented"))
    choice, _ = _client(fake).choose("hi", MENU)
    assert choice == "something invented"


@pytest.mark.parametrize(
    "response",
    [
        {"output": {}},
        {"output": {"message": {"content": []}}},
        {"output": {"message": {"content": [{"text": None}]}}},
        {},
    ],
)
def test_choose_maps_malformed_response_to_empty_string(response):
    """An empty/malformed model response becomes "" — never a menu member,
    so the caller always hard-rejects it."""
    fake = _FakeBedrockRuntime(response=response)
    choice, _ = _client(fake).choose("hi", MENU)
    assert choice == ""


def test_choose_propagates_transport_errors():
    """Transport/IAM/model failures raise — degrading the router surface is
    the caller's decision (#253 decision 4), never a silent default here."""
    fake = _FakeBedrockRuntime(error=RuntimeError("boom"))
    with pytest.raises(RuntimeError):
        _client(fake).choose("hi", MENU)
