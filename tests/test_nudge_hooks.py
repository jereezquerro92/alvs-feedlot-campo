from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCH_HOOK = ROOT / ".claude" / "hooks" / "dispatch_guardians.py"
API_HOOK = ROOT / ".claude" / "hooks" / "require_api_read.py"
PR_FLOW_HOOK = ROOT / ".claude" / "hooks" / "require_pr_flow.py"

# Coverage parity: reproduces today's dispatch_guardians.py WATCHLISTS
# glob-by-glob. adr-11 rule 5 keeps the watchlist in exactly two places
# (each guardian's Watchlist section + the hook WATCHLISTS); this test
# guards the hook half against silent drift when the two hooks were merged.
EXPECTED_WATCHLISTS = {
    "astro-drf-aws-prd": (
        "docs/PRD.md",
        "AGENTS.md",
        "CLAUDE.md",
        "README.md",
        ".github/workflows/*",
    ),
    "astro-drf-aws-adr": (
        "agents/*",
        ".claude/rules/*",
        "docs/adrs/*",
        "docs/obsolete/*",
        ".github/workflows/*",
        "compose.yaml",
        "docs/REQUIREMENTS.md",
        "docs/GLOSSARY.md",
        "docs/LOCALIZATION.md",
        "docs/INFRASTRUCTURE.md",
        "docs/VARIABLES.md",
        "docs/INVENTORY.md",
        "*/pyproject.toml",
        "pyproject.toml",
        "*/package.json",
        "package.json",
        "*/bun.lock*",
        "bun.lock*",
    ),
    "astro-drf-aws-api": (
        "docs/API.md",
        "*/urls.py",
        "*/views.py",
        "*/viewsets.py",
        "*/serializers.py",
        "*/models.py",
        "*/templates/*",
    ),
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise AssertionError(msg)


def ok(msg: str) -> None:
    print(f"ok  {msg}")


def run_dispatch(project_dir: Path, rel: str, session: str, tool: str = "Edit"):
    payload = json.dumps({
        "tool_name": tool,
        "session_id": session,
        "tool_input": {"file_path": str(project_dir / rel)},
    })
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    env.pop("CLAUDE_SESSION_ID", None)
    return subprocess.run(
        [sys.executable, str(DISPATCH_HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )


def run_api(prompt: str):
    payload = json.dumps({"prompt": prompt})
    return subprocess.run(
        [sys.executable, str(API_HOOK)],
        input=payload,
        capture_output=True,
        text=True,
    )


def run_pr_flow(command: str) -> subprocess.CompletedProcess:
    """Run require_pr_flow.py with a Bash tool_input command. The CWD is a bare
    tempdir so the best-effort gh/git enrichment resolves nothing — the
    deterministic base reminder is what gets exercised here."""
    payload = json.dumps({"tool_input": {"command": command}})
    with tempfile.TemporaryDirectory() as tmp:
        return subprocess.run(
            [sys.executable, str(PR_FLOW_HOOK)],
            input=payload,
            capture_output=True,
            text=True,
            cwd=tmp,
        )


def context_of(proc: subprocess.CompletedProcess) -> str:
    if not proc.stdout.strip():
        return ""
    return json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]


def test_guardian_named_once_across_eight_file_batch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        session = "S-batch"
        first = run_dispatch(project, "docs/adrs/adr-01.md", session)
        if "astro-drf-aws-adr" not in context_of(first):
            fail(
                "the first edit in the batch must name the ADR guardian; "
                f"got stdout={first.stdout!r}"
            )
        for n in range(2, 9):
            proc = run_dispatch(project, f"docs/adrs/adr-{n:02d}.md", session)
            if "astro-drf-aws-adr" in context_of(proc):
                fail(
                    f"edit {n} of the batch re-named the ADR guardian; the "
                    f"nudge must fire once per session, not per file. "
                    f"got stdout={proc.stdout!r}"
                )
        ok("guardian named once across an eight-file batch, not per file")


def test_api_gate_silent_on_false_positive() -> None:
    proc = run_api("the API gate is annoying")
    if proc.stdout.strip():
        fail(
            "a bare 'api' with no route-surface intent must not fire the "
            f"gate; got stdout={proc.stdout!r}"
        )
    ok("require_api_read silent on 'the API gate is annoying'")


def test_api_gate_fires_on_true_positive() -> None:
    proc = run_api("add an endpoint to the api")
    if "API.md" not in proc.stdout:
        fail(
            "a route-surface prompt must fire the gate and re-read "
            f"docs/API.md; got stdout={proc.stdout!r}"
        )
    ok("require_api_read fires on 'add an endpoint to the api'")


def load_watchlists() -> dict:
    spec = importlib.util.spec_from_file_location("dispatch_guardians", DISPATCH_HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.WATCHLISTS


def test_watchlist_coverage_parity() -> None:
    actual = load_watchlists()
    problems = []
    for guardian, globs in EXPECTED_WATCHLISTS.items():
        if guardian not in actual:
            problems.append(f"missing guardian key {guardian!r}")
            continue
        expected_set = set(globs)
        actual_set = set(actual[guardian])
        for dropped in sorted(expected_set - actual_set):
            problems.append(f"{guardian}: dropped glob {dropped!r}")
        for added in sorted(actual_set - expected_set):
            problems.append(f"{guardian}: added glob {added!r}")
    for guardian in sorted(set(actual) - set(EXPECTED_WATCHLISTS)):
        problems.append(f"unexpected guardian key {guardian!r}")
    if problems:
        fail(
            "merged WATCHLISTS diverged from today's coverage (adr-11 rule 5): "
            + "; ".join(problems)
        )
    ok("merged WATCHLISTS matches today's coverage file-by-file")


def test_pr_flow_nudges_on_worktree_remove() -> None:
    proc = run_pr_flow("git worktree remove .claude/worktrees/wf_test")
    if proc.returncode != 0:
        fail(
            "the hook must never deny a command; got "
            f"{proc.returncode} stderr={proc.stderr!r}"
        )
    out = proc.stdout.lower()
    if "rule 5" not in out or "after" not in out or "merge" not in out:
        fail(
            "git worktree remove must nudge the adr-19 rule-5 ordering "
            f"(remove after merge); got stdout={proc.stdout!r}"
        )
    ok("git worktree remove nudges the rule-5 ordering")


def test_pr_flow_silent_on_worktree_list_and_add() -> None:
    for command in ("git worktree list", "git worktree add foo bar"):
        proc = run_pr_flow(command)
        if proc.returncode != 0:
            fail(f"{command!r}: hook must never deny; got {proc.returncode}")
        if "rule 5" in proc.stdout.lower():
            fail(
                f"{command!r} must NOT fire the worktree-remove nudge "
                f"(regex false positive); got stdout={proc.stdout!r}"
            )
    ok("git worktree list/add do not trip the remove nudge")


def test_pr_flow_still_nudges_on_commit() -> None:
    proc = run_pr_flow("git commit -m x")
    if proc.returncode != 0:
        fail(f"hook must never deny a commit; got {proc.returncode}")
    if "issue -> (worktree optional) -> PR" not in proc.stdout:
        fail(
            "git commit must still print the existing issue->worktree->PR "
            f"nudge (regression guard); got stdout={proc.stdout!r}"
        )
    ok("git commit still prints the existing PR-flow nudge")


def main() -> int:
    tests = [
        test_guardian_named_once_across_eight_file_batch,
        test_api_gate_silent_on_false_positive,
        test_api_gate_fires_on_true_positive,
        test_watchlist_coverage_parity,
        test_pr_flow_nudges_on_worktree_remove,
        test_pr_flow_silent_on_worktree_list_and_add,
        test_pr_flow_still_nudges_on_commit,
    ]
    failed = 0
    for fn in tests:
        try:
            fn()
        except AssertionError:
            failed += 1
        except Exception as exc:
            print(f"FAIL: {fn.__name__}: {exc}", file=sys.stderr)
            failed += 1

    if failed:
        print(f"\n{failed} test(s) failed", file=sys.stderr)
        return 1
    print(f"\nall {len(tests)} test(s) passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
