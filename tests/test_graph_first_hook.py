
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "graph_first.py"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise AssertionError(msg)


def ok(msg: str) -> None:
    print(f"ok  {msg}")


def run_hook(
    tool_input: dict, remote: bool = False, project_dir=None
) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": "Grep", "tool_input": tool_input})
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir) if project_dir is not None else str(ROOT)
    env.pop("CLAUDE_CODE_REMOTE", None)
    if remote:
        env["CLAUDE_CODE_REMOTE"] = "true"
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )


def asks(proc: subprocess.CompletedProcess) -> bool:
    if not proc.stdout.strip():
        return False
    decision = json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"]
    return decision == "ask"


def test_repo_wide_bare_word_passes() -> None:
    proc = run_hook({"pattern": "guardian"})
    if asks(proc):
        fail(
            "a repo-wide search with no path is a text search until it names a "
            f"Python target; got stdout={proc.stdout!r}"
        )
    ok("repo-wide bare-word Grep no longer asks")


def test_explicit_py_symbol_still_asks() -> None:
    proc = run_hook({"pattern": "AccessRequest", "glob": "*.py"})
    if not asks(proc):
        fail(f"an explicit .py symbol hunt must still ask; got stdout={proc.stdout!r}")
    ok("explicit .py symbol search still asks")


def test_backend_path_symbol_still_asks() -> None:
    proc = run_hook({"pattern": "def bootstrap_admin", "path": "backend"})
    if not asks(proc):
        fail(f"a backend-path code search must still ask; got stdout={proc.stdout!r}")
    ok("backend-path code search still asks")


def test_docs_path_passes() -> None:
    proc = run_hook({"pattern": "lobby", "path": "docs"})
    if asks(proc):
        fail(f"docs/ prose is not the graph's business; got stdout={proc.stdout!r}")
    ok("docs/ search passes")


def test_cloud_session_never_asks() -> None:
    proc = run_hook({"pattern": "AccessRequest", "glob": "*.py"}, remote=True)
    if asks(proc):
        fail(
            "the graph is not vendored, so it does not exist in a cloud session; "
            f"an unanswerable ask would stall it. got stdout={proc.stdout!r}"
        )
    ok("cloud session never asks")


def test_reason_derives_project_id_from_checkout() -> None:
    proc = run_hook(
        {"pattern": "AccessRequest", "glob": "*.py"},
        project_dir="/home/kodex/Dev/Work/astro-drf-aws",
    )
    if not proc.stdout.strip():
        fail(f"an explicit .py symbol hunt must still ask; got stdout={proc.stdout!r}")
    reason = json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    if "home-kodex-Dev-Work-astro-drf-aws" not in reason:
        fail(
            "the project id must be derived from CLAUDE_PROJECT_DIR at runtime; "
            f"got reason={reason!r}"
        )
    if "home-kodex-Templates-astro-drf-aws" in reason:
        fail(
            "the stale hardcoded project id must never reappear in the reason; "
            f"got reason={reason!r}"
        )
    ok("reason derives project id from the current checkout")


def main() -> int:
    tests = [
        test_repo_wide_bare_word_passes,
        test_explicit_py_symbol_still_asks,
        test_backend_path_symbol_still_asks,
        test_docs_path_passes,
        test_cloud_session_never_asks,
        test_reason_derives_project_id_from_checkout,
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
