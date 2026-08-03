"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Advisor Bedrock client failure modes (#25 / #60) and async seam (#19)."""

import inspect

import pytest

from apps.advisors.inference import AdvisorBedrockClient
from apps.advisors.services import agenerate_report


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
    client = AdvisorBedrockClient.__new__(AdvisorBedrockClient)
    client.model_id = "test-advisor-model"
    client._client = fake
    return client


def _response(text):
    return {"output": {"message": {"content": [{"text": text}]}}}


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
def test_advisor_generate_raises_on_malformed_or_blank_response(response):
    fake = _FakeBedrockRuntime(response=response)
    with pytest.raises(RuntimeError):
        _client(fake).generate(system_prompt="sys", snapshot={"client": {"id": 1}})


def test_advisor_generate_propagates_transport_errors():
    fake = _FakeBedrockRuntime(error=RuntimeError("boom"))
    with pytest.raises(RuntimeError, match="boom"):
        _client(fake).generate(system_prompt="sys", snapshot={})


def test_agenerate_report_seam_is_awaitable():
    """adr-16 rule 4 seam stays importable and awaitable even without a caller (#19)."""
    assert inspect.iscoroutinefunction(agenerate_report)
