
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "check_variables.py"


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
    rows = "\n".join(f"| `{name}` | example | dev | some var |" for name in declared)
    (docs / "VARIABLES.md").write_text(
        "# VARIABLES\n\n"
        "| Name | Source | Env | Notes |\n"
        "|---|---|---|---|\n" + rows + "\n",
        encoding="utf-8",
    )
    return project


def test_env_helper_read_undeclared_is_caught() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = make_project(Path(tmp), declared=["DECLARED_VAR"])
        settings = project / "backend" / "config" / "settings.py"
        settings.parent.mkdir(parents=True)
        settings.write_text(
            'DEBUG = _env_bool("MISSING_HELPER_VAR", False)\n',
            encoding="utf-8",
        )
        proc = run_hook(project, settings)
        if proc.returncode != 2:
            fail(
                "hook must exit 2 for an undeclared variable read only via "
                f"_env_bool(); got {proc.returncode} stderr={proc.stderr!r}"
            )
        if "MISSING_HELPER_VAR" not in proc.stderr:
            fail(f"stderr must name the undeclared variable; got {proc.stderr!r}")
        ok("_env_bool() undeclared read is caught (regression guard)")


def test_env_helper_read_declared_passes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = make_project(Path(tmp), declared=["ALLOWED_HOST"])
        settings = project / "backend" / "config" / "settings.py"
        settings.parent.mkdir(parents=True)
        settings.write_text(
            'ALLOWED_HOSTS = _env_list("ALLOWED_HOST", "").split(",")\n'
            'HOST = _env("ALLOWED_HOST", "")\n',
            encoding="utf-8",
        )
        proc = run_hook(project, settings)
        if proc.returncode != 0:
            fail(
                "hook must pass when every _env*() read is declared; got "
                f"{proc.returncode} stderr={proc.stderr!r}"
            )
        ok("_env()/_env_list() declared reads pass")


def test_literal_os_environ_still_caught() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = make_project(Path(tmp), declared=[])
        module = project / "backend" / "app" / "views.py"
        module.parent.mkdir(parents=True)
        module.write_text(
            'import os\nSECRET = os.environ.get("SOME_LITERAL_VAR")\n',
            encoding="utf-8",
        )
        proc = run_hook(project, module)
        if proc.returncode != 2:
            fail(
                "hook must still catch literal os.environ.get() reads; got "
                f"{proc.returncode} stderr={proc.stderr!r}"
            )
        if "SOME_LITERAL_VAR" not in proc.stderr:
            fail(f"stderr must name the undeclared variable; got {proc.stderr!r}")
        ok("literal os.environ.get() undeclared read is still caught")


def test_repo_root_tests_dir_is_exempt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = make_project(Path(tmp), declared=[])
        script = project / "tests" / "test_aws_infra.py"
        script.parent.mkdir(parents=True)
        script.write_text(
            'import os\n'
            'PROFILE = os.environ.get("AWS_PROFILE", "kodex")\n'
            'REGION = os.environ.get("AWS_REGION", "us-east-1")\n',
            encoding="utf-8",
        )
        proc = run_hook(project, script)
        if proc.returncode != 0:
            fail(
                "hook must not flag env reads in repo-root tests/ tooling "
                f"scripts (issue #138); got {proc.returncode} "
                f"stderr={proc.stderr!r}"
            )
        ok("repo-root tests/ tooling env reads are exempt (issue #138)")


def test_backend_test_files_still_swept() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = make_project(Path(tmp), declared=[])
        module = project / "backend" / "apps" / "users" / "test_cognito_live.py"
        module.parent.mkdir(parents=True)
        module.write_text(
            'import os\nSECRET_ID = os.environ.get("SOME_APP_TEST_VAR")\n',
            encoding="utf-8",
        )
        proc = run_hook(project, module)
        if proc.returncode != 2:
            fail(
                "the tests/ exemption must not leak to backend app test "
                f"files; got {proc.returncode} stderr={proc.stderr!r}"
            )
        ok("backend app test files remain in the sweep")


def test_harness_scripts_are_exempt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = make_project(Path(tmp), declared=[])
        script = project / "scripts" / "mvmcp.py"
        script.parent.mkdir(parents=True)
        script.write_text(
            'import os\n'
            'HOST = os.environ.get("MARKDOWN_VAULT_MCP_HOST", "127.0.0.1")\n',
            encoding="utf-8",
        )
        proc = run_hook(project, script)
        if proc.returncode != 0:
            fail(
                "harness tooling under scripts/ is not app runtime — VARIABLES "
                "governs what backend/frontend read (adr-03 rule 7; adr-18 rule 3 "
                f"says so outright for the vault launcher); got {proc.returncode} "
                f"stderr={proc.stderr!r}"
            )
        ok("scripts/ harness tooling env reads are exempt")


def test_committed_env_template_still_swept() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = make_project(Path(tmp), declared=[])
        template = project / ".env.example"
        template.write_text("SOME_UNDECLARED_VAR=value\n", encoding="utf-8")
        proc = run_hook(project, template)
        if proc.returncode != 2:
            fail(
                "the committed root .env template must stay in the sweep; got "
                f"{proc.returncode} stderr={proc.stderr!r}"
            )
        ok("root .env* templates remain in the sweep")


def test_frontend_tree_is_swept() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = make_project(Path(tmp), declared=[])
        page = project / "frontend" / "src" / "pages" / "index.astro"
        page.parent.mkdir(parents=True)
        page.write_text(
            'const url = process.env.SOME_FRONTEND_VAR ?? "";\n',
            encoding="utf-8",
        )
        proc = run_hook(project, page)
        if proc.returncode != 2:
            fail(
                "the frontend service tree must stay in the sweep; got "
                f"{proc.returncode} stderr={proc.stderr!r}"
            )
        ok("frontend/ service tree remains in the sweep")


def main() -> int:
    tests = [
        test_env_helper_read_undeclared_is_caught,
        test_env_helper_read_declared_passes,
        test_literal_os_environ_still_caught,
        test_repo_root_tests_dir_is_exempt,
        test_backend_test_files_still_swept,
        test_harness_scripts_are_exempt,
        test_committed_env_template_still_swept,
        test_frontend_tree_is_swept,
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
