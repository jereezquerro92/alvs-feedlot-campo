
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise AssertionError(msg)


def ok(msg: str) -> None:
    print(f"ok  {msg}")


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing file {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def test_required_docs_and_compose() -> None:
    for path in (
        ROOT / "compose.yaml",
        ROOT / ".env.example",
        ROOT / "docs" / "DOCKER.md",
        ROOT / ".claude" / "rules" / "adr-09-docker-compose.md",
    ):
        if not path.exists():
            fail(f"missing {path.relative_to(ROOT)}")
    ok("compose + docker docs present")


def test_compose_db_contract() -> None:
    text = read(ROOT / "compose.yaml")
    if "db:" not in text:
        fail("compose.yaml must define service db")
    if "postgres:17" not in text:
        fail("compose.yaml must pin postgres 17.x")
    for profile in ('"db"', '"backend"', '"full"'):
        if profile not in text:
            fail(f"compose.yaml missing profile token {profile}")
    if "pg_isready" not in text:
        fail("db healthcheck must use pg_isready")
    ok("compose db contract")


def test_no_per_app_compose() -> None:
    for path in (
        ROOT / "backend" / "docker-compose.yaml",
        ROOT / "backend" / "compose.yaml",
        ROOT / "frontend" / "docker-compose.yaml",
        ROOT / "frontend" / "compose.yaml",
    ):
        if path.exists():
            fail(f"per-app compose not allowed by default: {path.relative_to(ROOT)}")
    ok("no per-app compose files")


def test_docs_reserve_app_paths() -> None:
    docker = read(ROOT / "docs" / "DOCKER.md")
    adr = read(ROOT / ".claude" / "rules" / "adr-09-docker-compose.md")
    for blob, label in ((docker, "DOCKER.md"), (adr, "adr-09")):
        if "backend/" not in blob or "frontend/" not in blob:
            fail(f"{label} must reserve backend/ and frontend/ paths")
        if "stage 3" not in blob.lower() and "stage 3" not in blob:
            if "stage 3" not in blob:
                fail(f"{label} must state apps are stage 3 / not harness-scaffolded")
    ok("docs reserve paths; apps are stage 3")


def test_env_example_names() -> None:
    example = read(ROOT / ".env.example")
    for name in ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"):
        if name not in example:
            fail(f".env.example missing {name}")
    ok(".env.example covers DB VARIABLES names")


def test_docker_compose_config() -> None:
    for profile in ("db", "full"):
        cmd = [
            "docker",
            "compose",
            "--project-directory",
            str(ROOT),
            "-f",
            str(ROOT / "compose.yaml"),
            "--profile",
            profile,
            "config",
            "--quiet",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        if proc.returncode != 0:
            fail(
                f"docker compose --profile {profile} config failed:\n"
                f"{proc.stderr or proc.stdout}"
            )
    ok("docker compose config (db + full profiles)")


def compose_cmd(*args: str) -> list[str]:
    return [
        "docker",
        "compose",
        "--project-directory",
        str(ROOT),
        "-f",
        str(ROOT / "compose.yaml"),
        *args,
    ]


def test_smoke_db() -> None:
    env = os.environ.copy()
    port = env.get("SMOKE_DB_PORT", "55432")
    env["DB_PUBLISH_PORT"] = port

    subprocess.run(
        compose_cmd("--profile", "db", "down", "-v", "--remove-orphans"),
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=env,
    )

    print(f"smoke: starting db on host port {port}…")
    proc = subprocess.run(
        compose_cmd(
            "--profile",
            "db",
            "up",
            "-d",
            "--wait",
            "--wait-timeout",
            "120",
        ),
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=env,
    )
    if proc.returncode != 0:
        logs = subprocess.run(
            compose_cmd("--profile", "db", "logs", "--no-color", "--tail", "40"),
            capture_output=True,
            text=True,
            cwd=ROOT,
            env=env,
        )
        fail(
            "compose db up --wait failed:\n"
            f"{proc.stderr or proc.stdout}\n--- logs ---\n{logs.stdout}\n{logs.stderr}"
        )

    deadline = time.time() + 30
    ready = False
    while time.time() < deadline:
        check = subprocess.run(
            compose_cmd(
                "--profile",
                "db",
                "exec",
                "-T",
                "db",
                "pg_isready",
                "-U",
                env.get("DB_USER", "app"),
                "-d",
                env.get("DB_NAME", "app"),
            ),
            capture_output=True,
            text=True,
            cwd=ROOT,
            env=env,
        )
        if check.returncode == 0:
            ready = True
            break
        time.sleep(1)

    if not ready:
        fail("db not ready via pg_isready after smoke")
    ok("smoke: postgres db healthy")

    subprocess.run(
        compose_cmd("--profile", "db", "down", "-v"),
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=env,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="start live db profile and pg_isready",
    )
    args = parser.parse_args()
    os.chdir(ROOT)

    tests = [
        test_required_docs_and_compose,
        test_compose_db_contract,
        test_no_per_app_compose,
        test_docs_reserve_app_paths,
        test_env_example_names,
        test_docker_compose_config,
    ]
    if args.smoke:
        tests.append(test_smoke_db)

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
