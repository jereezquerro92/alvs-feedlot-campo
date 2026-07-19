"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-15-chatbot-two-tier]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[CHATBOT]]
LIVE-DOC:END"""

"""The blocking Bedrock connectivity gate as a pytest test (#253).

Marked `bedrock_live`: excluded from the default suite (like `cognito_live`)
and run explicitly by the deploy pipeline with OIDC credentials, where it
HARD-FAILS on any unreachability — network, IAM grant, or model access.
It wraps the same `check_bedrock_connectivity` command a developer runs
from the terminal, so both gate entrances prove the identical real path.
"""

import pytest
from django.core.management import call_command

pytestmark = pytest.mark.bedrock_live


def test_bedrock_connectivity_gate_hard_fails_on_unreachable():
    # CommandError (or any boto3 failure) propagates and fails the run —
    # there is no warning path.
    call_command("check_bedrock_connectivity")
