#!/usr/bin/env python3
"""sessionStart: inject the sense-rewrite gate (skill still decides when to fire)."""
from __future__ import annotations

import json
import sys

_CONTEXT = (
    "sense-rewrite gate: apply the sense-rewrite skill ONLY if this turn's "
    "user message has Spanish you must translate to act, or English that could "
    "be understood two ways and would change the task. Format: > corrected "
    "native American English, then ---, then the answer. Skip trivial typos. "
    "Skip when kdx-triage owns the turn."
)


def main() -> None:
    try:
        json.load(sys.stdin)
    except json.JSONDecodeError:
        pass
    print(json.dumps({"additional_context": _CONTEXT}))


if __name__ == "__main__":
    main()
