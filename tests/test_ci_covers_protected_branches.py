from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github" / "workflows" / "ci.yml"

# Guards the deadlock of issue #57. `prod`'s branch protection requires the
# status-check contexts this workflow produces, with `enforce_admins: true`.
# That makes two things load-bearing, and neither is visible from inside the
# workflow file:
#
#   1. `pull_request.branches` must include every protected branch. A promotion
#      PR into a branch the trigger omits never starts CI, so its required
#      contexts are never reported and it can never merge — not even with
#      `--admin`. The branch becomes unreachable, which is how `prod` sat
#      until #57: silently, because the failure mode is an absent check
#      rather than a red one.
#
#   2. The job ids must keep their exact names. Protection matches contexts by
#      string, so renaming `harness` to `harness-tests` leaves protection
#      waiting on a context nothing emits — the same deadlock through a
#      different door.
#
# Protection itself lives in the repo, not in git ([[adr-19-issue-worktree-pr]]
# rule 4), so this test cannot read it. It asserts the side git owns, and the
# constants below are the contract: change them only alongside the protection
# settings they mirror.

PROTECTED_BRANCHES = ("main", "prod")
REQUIRED_CONTEXTS = {"backend", "frontend", "harness"}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise AssertionError(msg)


def ok(msg: str) -> None:
    print(f"ok  {msg}")


def _ci_source() -> str:
    if not CI.is_file():
        fail(f"missing {CI.relative_to(ROOT)}")
    return CI.read_text(encoding="utf-8")


def test_pull_request_trigger_covers_every_protected_branch() -> None:
    source = _ci_source()

    match = re.search(r"^\s*branches:\s*\[([^\]]*)\]", source, re.MULTILINE)
    if not match:
        fail(
            "ci.yml declares no inline `branches: [...]` filter — if the trigger "
            "moved to a block list, update this test to parse it rather than "
            "deleting the check (issue #57)"
        )

    listed = {b.strip().strip("\"'") for b in match.group(1).split(",") if b.strip()}
    missing = [b for b in PROTECTED_BRANCHES if b not in listed]
    if missing:
        fail(
            f"ci.yml's pull_request trigger omits protected branch(es) {missing}: "
            f"protection on them requires contexts {sorted(REQUIRED_CONTEXTS)}, so a "
            f"PR into them can never merge — CI never starts and the checks are "
            f"never reported (issue #57)"
        )
    ok(f"pull_request trigger covers {sorted(listed)}")


def test_job_ids_match_the_required_status_check_contexts() -> None:
    source = _ci_source()

    _, _, jobs_block = source.partition("\njobs:\n")
    if not jobs_block:
        fail("ci.yml has no top-level `jobs:` block")

    job_ids = set(re.findall(r"^  ([A-Za-z][\w-]*):$", jobs_block, re.MULTILINE))
    if job_ids != REQUIRED_CONTEXTS:
        fail(
            f"ci.yml's job ids {sorted(job_ids)} no longer match the status-check "
            f"contexts branch protection requires, {sorted(REQUIRED_CONTEXTS)}. "
            f"Protection matches contexts by name, so a rename here blocks every "
            f"PR into a protected branch until the settings are updated too "
            f"(issue #57)"
        )
    ok(f"job ids match required contexts {sorted(REQUIRED_CONTEXTS)}")


if __name__ == "__main__":
    test_pull_request_trigger_covers_every_protected_branch()
    test_job_ids_match_the_required_status_check_contexts()
