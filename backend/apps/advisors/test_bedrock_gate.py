"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-16-async-mandatory]] · [[adr-27-advisors-generative]]
Docs: [[BACKEND]] · [[FEEDLOT]]
LIVE-DOC:END"""

"""The blocking advisor Bedrock connectivity gate as a pytest test.

Twin of the router's `test_bedrock_gate` (adr-31 pending point). Marked
`bedrock_live`: excluded from the default suite (like `cognito_live`) and run
explicitly by the deploy pipeline with OIDC credentials, where it HARD-FAILS on
any unreachability — network, IAM grant, or model access on
`ADVISOR_BEDROCK_MODEL_ID`. It wraps the same
`check_advisor_bedrock_connectivity` command a developer runs from the terminal,
so both gate entrances prove the identical real generative path.
"""

import pytest
from django.core.management import call_command

pytestmark = pytest.mark.bedrock_live


def test_advisor_bedrock_connectivity_gate_hard_fails_on_unreachable():
    # CommandError (or any boto3 failure) propagates and fails the run —
    # there is no warning path.
    call_command("check_advisor_bedrock_connectivity")
