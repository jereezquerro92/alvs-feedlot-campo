"""Tests for docs/hooks/guardian-dispatch --bundle (adr-03 rule 10).

Stdlib only — no third-party deps. Mirrors the structure of test_nudge_hooks.py.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "docs" / "hooks" / "guardian-dispatch"

# Minimal agent frontmatter with a watch: list that matches adr-*.md files.
FAKE_AGENT_MD = """\
---
name: fake-guardian
description: Minimal guardian for tests.
model: sonnet
watch:
  - docs/adrs/*
---

Fake guardian body.
"""

# Minimal ADR frontmatter with category + use_case so the adr_index has content.
FAKE_ADR_MD = """\
---
title: adr-99-test
type: adr
category: harness
use_case: testing the bundle dispatch payload
created: 2026-08-03
modified: 2026-08-03
tags: [adr, test]
---

# ADR-99 — test only
"""


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise AssertionError(msg)


def ok(msg: str) -> None:
    print(f"ok  {msg}")


def make_git_repo() -> Path:
    """Create a temp directory with a minimal git repo and agent/ADR structure."""
    tmp = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init"], cwd=tmp, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp, capture_output=True, check=True,
    )

    # Create docs/agents/ with a fake guardian definition.
    agents_dir = tmp / "docs" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "fake-guardian.md").write_text(FAKE_AGENT_MD, encoding="utf-8")

    # Create docs/adrs/ with a fake ADR so adr_index has something to emit.
    adrs_dir = tmp / "docs" / "adrs"
    adrs_dir.mkdir(parents=True)
    (adrs_dir / "adr-99-test.md").write_text(FAKE_ADR_MD, encoding="utf-8")

    # Initial commit so HEAD exists.
    subprocess.run(
        ["git", "add", "-A"], cwd=tmp, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmp, capture_output=True, check=True,
    )
    return tmp


def run_dispatch(repo: Path, *extra_args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    return subprocess.run(
        [sys.executable, str(DISPATCH), *extra_args],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )


def test_empty_batch_exits_zero() -> None:
    """Empty batch (no changes) → exit 0, no guardian owed."""
    repo = make_git_repo()
    proc = run_dispatch(repo)
    if proc.returncode != 0:
        fail(
            f"empty batch must exit 0; got {proc.returncode} "
            f"stdout={proc.stdout!r}"
        )
    if "no guardian owed" not in proc.stdout:
        fail(f"empty batch must say 'no guardian owed'; got {proc.stdout!r}")
    ok("empty batch exits 0 with 'no guardian owed'")


def test_unwatched_file_exits_zero() -> None:
    """A changed file that no guardian watches → exit 0."""
    repo = make_git_repo()
    # Add a file outside the watch: glob (docs/adrs/*).
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    proc = run_dispatch(repo)
    if proc.returncode != 0:
        fail(
            f"unwatched file must exit 0; got {proc.returncode} "
            f"stdout={proc.stdout!r}"
        )
    if "no guardian owed" not in proc.stdout:
        fail(f"unwatched file must say 'no guardian owed'; got {proc.stdout!r}")
    ok("unwatched file exits 0 with 'no guardian owed'")


def test_name_only_exits_one_and_names_guardian() -> None:
    """A watched changed file without --bundle → exit 1, guardian named."""
    repo = make_git_repo()
    (repo / "docs" / "adrs" / "adr-01-new.md").write_text(
        "# new adr\n", encoding="utf-8"
    )
    proc = run_dispatch(repo)
    if proc.returncode != 1:
        fail(
            f"watched file must exit 1; got {proc.returncode} "
            f"stdout={proc.stdout!r}"
        )
    if "fake-guardian" not in proc.stdout:
        fail(f"guardian name must appear in output; got {proc.stdout!r}")
    if "--bundle" not in proc.stdout:
        fail(f"name-only must hint to re-run with --bundle; got {proc.stdout!r}")
    ok("name-only exits 1 and hints --bundle re-run")


def test_bundle_shape_rule10_sonnet_no_cheap() -> None:
    """--bundle output matches adr-03 rule 10: header, sonnet tier, no cheap."""
    repo = make_git_repo()
    (repo / "docs" / "adrs" / "adr-01-new.md").write_text(
        "# new adr\n", encoding="utf-8"
    )
    proc = run_dispatch(repo, "--bundle")
    if proc.returncode != 1:
        fail(
            f"--bundle with watched file must exit 1; got {proc.returncode} "
            f"stdout={proc.stdout!r}"
        )
    out = proc.stdout

    # Must carry the rule 10 header.
    if "--- bundle (adr-03 rule 10) ---" not in out:
        fail(
            f"bundle header must be '--- bundle (adr-03 rule 10) ---'; "
            f"got:\n{out}"
        )

    # Tier must be sonnet (rule 9 override).
    if "tier: sonnet" not in out:
        fail(f"bundle must emit 'tier: sonnet'; got:\n{out}")

    # Must never say cheap anywhere.
    if "cheap" in out:
        fail(f"'cheap' must not appear in bundle output; got:\n{out}")

    # adr_index section must be present.
    if "## adr_index" not in out:
        fail(f"bundle must contain '## adr_index' section; got:\n{out}")

    # adr_index must contain the fake ADR we planted.
    if "adr-99-test.md" not in out:
        fail(
            f"adr_index must list the fake ADR adr-99-test.md; got:\n{out}"
        )

    # diff section must be present.
    if "## diff" not in out:
        fail(f"bundle must contain '## diff' section; got:\n{out}")

    ok("--bundle shape: rule 10 header, sonnet tier, no cheap, adr_index, diff")


def main() -> int:
    tests = [
        test_empty_batch_exits_zero,
        test_unwatched_file_exits_zero,
        test_name_only_exits_one_and_names_guardian,
        test_bundle_shape_rule10_sonnet_no_cheap,
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
