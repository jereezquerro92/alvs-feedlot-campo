#!/usr/bin/env python3
"""API mention gate (UserPromptSubmit).

A prompt that plausibly touches the route surface forces a fresh read of
docs/API.md before acting: the file is the only source of valid endpoints
(adr-03) and may have changed since the session-start preload. The matcher
targets route-surface-plausible prompts, not any mention of the word "api" —
a bare "api" that never means the route surface ("the API gate is annoying")
no longer fires. Stdout is added to context; any internal error exits 0.
"""

import json
import re
import sys

MENTION = re.compile(
    r"""
      /api/                                                  # a literal route path
    | \bendpoint                                             # endpoint(s)
    | \bviewset                                              # DRF viewset(s)
    | \bserializer                                           # DRF serializer(s)
    | \burls\.py\b                                           # the routing module
    | \bDRF\b                                                # the framework by name
    | \b(?:add|adds|adding|chang\w*|remov\w*|declar\w*)\b    # an action verb ...
        [\s\S]{0,30}\bapi\b                                  #   ... near "api"
    | \bapi\b                                                # "api" ...
        [\s\S]{0,30}
        \b(?:add|adds|adding|chang\w*|remov\w*|declar\w*)\b  #   ... near an action verb
    """,
    re.IGNORECASE | re.VERBOSE,
)


def main():
    try:
        payload = json.load(sys.stdin)
        prompt = payload.get("prompt", "")
        if not MENTION.search(prompt):
            return 0
        print(
            "API gate: this prompt mentions the API. Before acting on it, Read "
            "docs/API.md — it is the only source of valid endpoints (adr-03) and "
            "the in-memory copy may be stale. Every endpoint decision must match "
            "its rows; a needed endpoint missing there gets its row added first."
        )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
