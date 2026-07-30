
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


def test_backend_startup_chain_rebuilds_the_database() -> None:
    """A destroyed-and-rebuilt stack must come up populated (issue #59).

    The failure this guards is silent: drop `seed_demo_feedlot` and the stack
    still builds, still passes health checks, and still serves every page — it
    just serves them empty, which reads as "the backend is broken" rather than
    "nobody ran the seed". Nothing else in the suite would notice.
    """
    text = read(ROOT / "compose.yaml")
    # Narrow to the command itself, not the service block around it: the
    # surrounding comments talk *about* the chain, and matching on those would
    # let prose pass for behaviour.
    _, _, backend_block = text.partition("\n  backend:")
    _, _, after_command = backend_block.partition("\n    command:")
    command, _, _ = after_command.partition("\n    volumes:")
    if not command.strip():
        fail("compose.yaml: cannot locate the backend service's command block")

    for step in (
        "migrate --noinput",
        "bootstrap_admin",
        "seed_demo_operator",
        "seed_demo_feedlot",
        "createcachetable",
    ):
        if step not in command:
            fail(
                f"compose.yaml: the backend startup chain no longer runs `{step}`. "
                f"Every step rebuilds part of the database a `down -v` destroyed; "
                f"dropping one yields a stack that boots healthy and wrong (issue #59)"
            )

    if "seed_demo_feedlot --if-debug" not in command:
        fail(
            "compose.yaml: seed_demo_feedlot must be called with --if-debug. The "
            "chain is joined by `&&`, so outside DEBUG the command's CommandError "
            "would abort the boot and leave the backend down (issue #59)"
        )

    if "|| true" in command or "|| :" in command:
        fail(
            "compose.yaml: the backend startup chain must not swallow failures. "
            "--if-debug skips the one expected non-failure; everything else that "
            "goes wrong during boot has to be loud (issue #59)"
        )

    seed = read(
        ROOT / "backend" / "apps" / "clients" / "management" / "commands" / "seed_demo_feedlot.py"
    )
    if '"--if-debug"' not in seed:
        fail(
            "backend seed_demo_feedlot no longer accepts --if-debug, but compose.yaml "
            "passes it: argparse would reject the flag and abort the boot (issue #59)"
        )
    if "DEMO_TAX_IDS" not in seed or ".exists()" not in seed:
        fail(
            "backend seed_demo_feedlot lost its already-seeded short-circuit. The "
            "startup chain runs on every `up`, including one over a surviving "
            "volume, so the command must stay idempotent (issue #59)"
        )
    ok("backend startup chain rebuilds and seeds the database")


def test_frontend_start_clears_the_stale_dev_marker() -> None:
    """A rebuilt stack must bring the frontend up too (issue #60).

    `astro dev` records its owning PID in `.astro/dev.json`, and the bind mount
    puts that file on the host, so it outlives the container. The next container
    resolves that PID against its own namespace — where an unrelated process may
    hold the same low number — and refuses to start. The failure is intermittent,
    which is why it survived unnoticed: `up` succeeds, and only `ps -a` shows
    `frontend Exited (1)` beside two healthy siblings.
    """
    text = read(ROOT / "compose.yaml")
    _, _, frontend_block = text.partition("\n  frontend:")
    _, _, after_command = frontend_block.partition("\n    command:")
    command, _, _ = after_command.partition("\n    volumes:")
    if not command.strip():
        fail("compose.yaml: cannot locate the frontend service's command block")

    if ".astro/dev.json" not in command:
        fail(
            "compose.yaml: the frontend command no longer clears .astro/dev.json "
            "before starting. A stale marker from a previous container makes "
            "`astro dev` refuse to start, intermittently (issue #60)"
        )
    if "bun run dev" not in command:
        fail("compose.yaml: the frontend must still run the bun dev server ([[FRONTEND]])")
    if "npm" in command:
        fail("compose.yaml: npm is prohibited ([[adr-04-frontend-and-design-system]] rule 2)")
    ok("frontend start clears the stale astro dev marker")


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
        test_backend_startup_chain_rebuilds_the_database,
        test_frontend_start_clears_the_stale_dev_marker,
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
