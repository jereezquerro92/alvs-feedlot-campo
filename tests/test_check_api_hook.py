
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "check_api.py"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise AssertionError(msg)


def ok(msg: str) -> None:
    print(f"ok  {msg}")


def run_hook(project_dir: Path, file_path: Path) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_input": {"file_path": str(file_path)}})
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )


def make_project(tmp_path: Path, declared: list[str]) -> Path:
    project = tmp_path / "project"
    docs = project / "docs"
    docs.mkdir(parents=True)
    rows = "\n".join(f"| GET | `{path}` | View | none | note |" for path in declared)
    (docs / "API.md").write_text(
        "# API\n\n"
        "| Method | Path | View | Auth | Notes |\n"
        "|---|---|---|---|---|\n" + rows + "\n",
        encoding="utf-8",
    )
    return project


def write_urls(project: Path, body: str) -> Path:
    urls = project / "backend" / "apps" / "x" / "urls.py"
    urls.parent.mkdir(parents=True)
    urls.write_text(body, encoding="utf-8")
    return urls


def test_full_path_bypass_is_rejected() -> None:
    # Two UNRELATED declared rows: one holds "users", the other holds "archive".
    # Under the OLD per-segment logic each segment matched a different row and
    # the hook returned 0 — the exact false negative this test locks out.
    with tempfile.TemporaryDirectory() as tmp:
        project = make_project(
            Path(tmp), declared=["/api/users/", "/api/archive/logs/"]
        )
        urls = write_urls(
            project,
            'from django.urls import path\n'
            'urlpatterns = [path("users/<id>/archive/", ArchiveView.as_view())]\n',
        )
        proc = run_hook(project, urls)
        if proc.returncode != 2:
            fail(
                "hook must exit 2 for a multi-segment route whose full path is "
                "undeclared, even when each segment appears in some unrelated "
                f"row; got {proc.returncode} stderr={proc.stderr!r}"
            )
        if "users/<id>/archive/" not in proc.stderr:
            fail(f"stderr must name the undeclared route; got {proc.stderr!r}")
        ok("full-path bypass (segments split across unrelated rows) is rejected")


def test_declared_full_path_passes() -> None:
    # Same route, but now the full path is declared as one row — a param
    # segment (<id>) in the declared path must not break the ordered match.
    with tempfile.TemporaryDirectory() as tmp:
        project = make_project(
            Path(tmp), declared=["/api/users/", "/api/users/<id>/archive/"]
        )
        urls = write_urls(
            project,
            'from django.urls import path\n'
            'urlpatterns = [path("users/<id>/archive/", ArchiveView.as_view())]\n',
        )
        proc = run_hook(project, urls)
        if proc.returncode != 0:
            fail(
                "adding a matching row for the full path must make the write "
                f"pass; got {proc.returncode} stderr={proc.stderr!r}"
            )
        ok("declared full path passes (param segment is skippable filler)")


def test_existing_template_routes_pass() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = make_project(
            Path(tmp),
            declared=[
                "/api/health/",
                "/accounts/login/",
                "/api/me/",
                "/api/m365/hello/",
                "/api/m365/world/",
                "/api/router/route/",
                "/admin/",
            ],
        )
        urls = write_urls(
            project,
            'from django.urls import path\n'
            'urlpatterns = [\n'
            '    path("health/", HealthCheckView.as_view(), name="health"),\n'
            '    path("m365/hello/", views.HelloView.as_view(), name="hello"),\n'
            '    path("m365/world/", views.WorldView.as_view(), name="world"),\n'
            '    path("router/route/", views.RouteView.as_view(), name="route"),\n'
            ']\n',
        )
        proc = run_hook(project, urls)
        if proc.returncode != 0:
            fail(
                "already-declared template routes must keep passing after the "
                f"fix; got {proc.returncode} stderr={proc.stderr!r}"
            )
        ok("existing declared template routes continue to pass")


def test_undeclared_single_segment_still_caught() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = make_project(Path(tmp), declared=["/api/health/"])
        urls = write_urls(
            project,
            'from django.urls import path\n'
            'urlpatterns = [path("secret/", V.as_view())]\n',
        )
        proc = run_hook(project, urls)
        if proc.returncode != 2:
            fail(
                "the base case (a single undeclared segment) must still be "
                f"caught; got {proc.returncode} stderr={proc.stderr!r}"
            )
        if "secret" not in proc.stderr:
            fail(f"stderr must name the undeclared route; got {proc.stderr!r}")
        ok("undeclared single-segment route is still caught")


def main() -> int:
    tests = [
        test_full_path_bypass_is_rejected,
        test_declared_full_path_passes,
        test_existing_template_routes_pass,
        test_undeclared_single_segment_still_caught,
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
