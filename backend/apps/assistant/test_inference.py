"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Assistant Bedrock client payload shape and failure modes (#13, #25 / #60)."""

import pytest

from apps.assistant.inference import AssistantBedrockClient


class _FakeBedrockRuntime:
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
    client = AssistantBedrockClient.__new__(AssistantBedrockClient)
    client.model_id = "test-assistant-model"
    client._client = fake
    return client


def _response(text):
    return {"output": {"message": {"content": [{"text": text}]}}}


def test_generate_does_not_duplicate_trailing_user_turn():
    """History that already ends in the user question must not become two
    consecutive user roles in the Converse payload (#13 / #60)."""
    fake = _FakeBedrockRuntime(response=_response("ok"))
    history = [
        {"role": "user", "text": "primera"},
        {"role": "assistant", "text": "respuesta"},
        {"role": "user", "text": "segunda"},
    ]
    text, model_id, _, _ = _client(fake).generate(
        snapshot={"client": {"id": 1}}, history=history, question="segunda"
    )
    assert text == "ok"
    assert model_id == "test-assistant-model"
    roles = [m["role"] for m in fake.calls[0]["messages"]]
    assert roles == ["user", "assistant", "user"]
    # No two consecutive user roles.
    assert all(a != b or a != "user" for a, b in zip(roles, roles[1:]))


def test_generate_prior_history_only_stays_alternating():
    fake = _FakeBedrockRuntime(response=_response("ok"))
    history = [
        {"role": "user", "text": "primera"},
        {"role": "assistant", "text": "respuesta"},
    ]
    _client(fake).generate(
        snapshot={"client": {"id": 1}}, history=history, question="nueva"
    )
    roles = [m["role"] for m in fake.calls[0]["messages"]]
    assert roles == ["user", "assistant", "user"]


@pytest.mark.parametrize(
    "response",
    [
        {"output": {}},
        {"output": {"message": {"content": []}}},
        {"output": {"message": {"content": [{"text": None}]}}},
        {"output": {"message": {"content": [{"text": "   "}]}}},
        {},
    ],
)
def test_generate_raises_on_malformed_or_blank_response(response):
    fake = _FakeBedrockRuntime(response=response)
    with pytest.raises(RuntimeError):
        _client(fake).generate(
            snapshot={}, history=[], question="hola"
        )


def test_generate_propagates_transport_errors():
    fake = _FakeBedrockRuntime(error=RuntimeError("boom"))
    with pytest.raises(RuntimeError, match="boom"):
        _client(fake).generate(snapshot={}, history=[], question="hola")
