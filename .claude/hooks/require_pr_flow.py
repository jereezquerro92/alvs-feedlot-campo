#!/usr/bin/env python3
"""Issue -> Worktree -> PR nudge (PreToolUse on Bash).

Layer 2 of the enforcement stack in adr-19-issue-worktree-pr: a bypassable local
reminder, never the boundary. It fires on a git commit or a push at main/prod and
prints the flow to context; it also fires on a `git worktree remove` to nudge the
rule-5 ordering (remove only after the PR merges, never before). It never denies
(exit 0 always). The only inviolable gate is GitHub branch protection, which this
template does not ship (adr-19 rule 4).
"""

import json
import re
import subprocess
import sys

COMMIT = re.compile(r"\bgit\s+commit\b")
PUSH_PROTECTED = re.compile(r"\bgit\s+push\b.*\b(main|prod)\b")
WORKTREE_REMOVE = re.compile(r"\bgit\s+worktree\s+remove\b")


def _open_pr_note(cmd):
    """Best-effort, fail-open enrichment: if the worktree being removed still
    has an OPEN PR, name it. Any failure (no git/gh, timeout, empty result)
    returns None and the caller falls back to the base reminder."""
    try:
        # First non-flag token after `remove` is the worktree path.
        tokens = cmd.split()
        try:
            idx = tokens.index("remove")
        except ValueError:
            return None
        path = None
        for tok in tokens[idx + 1:]:
            if not tok.startswith("-"):
                path = tok
                break
        if not path:
            return None
        branch = subprocess.run(
            ["git", "-C", path, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        if not branch:
            return None
        out = subprocess.run(
            ["gh", "pr", "list", "--head", branch, "--state", "open",
             "--json", "number"],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        prs = json.loads(out) if out else []
        numbers = [str(pr.get("number")) for pr in prs if pr.get("number")]
        if not numbers:
            return None
        return (
            "PR #" + ", #".join(numbers) + " for branch " + branch +
            " is still OPEN: removing this worktree now is early per adr-19 "
            "rule 5 (remove on merge, not before)."
        )
    except Exception:
        return None


def main():
    try:
        payload = json.load(sys.stdin)
        cmd = payload.get("tool_input", {}).get("command", "")
        if COMMIT.search(cmd) or PUSH_PROTECTED.search(cmd):
            print(
                "PR-flow nudge (adr-19-issue-worktree-pr): every change is "
                "issue -> (worktree optional) -> PR; main is reached only by merging a "
                "PR, never by a direct hand-commit. Integrate as the gh/kodexArg "
                "identity, then delete the worktree (git worktree remove) and branch. "
                "This is a reminder, not a gate."
            )
        if WORKTREE_REMOVE.search(cmd):
            note = _open_pr_note(cmd)
            print(
                "Worktree-removal nudge (adr-19-issue-worktree-pr rule 5): a "
                "worktree is removed only AFTER its PR has merged, never before "
                "— no worktree outlives its PR, but neither does it die ahead of "
                "one. Confirm the PR reached its terminal outcome first."
                + (" " + note if note else "")
                + " This is a reminder, not a gate."
            )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
