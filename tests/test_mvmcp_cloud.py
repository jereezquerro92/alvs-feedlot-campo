
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "mvmcp.py"
SETUP = ROOT / "scripts" / "cloud_setup.sh"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise AssertionError(msg)


def ok(msg: str) -> None:
    print(f"ok  {msg}")


def load(env: dict):
    saved = dict(os.environ)
    os.environ.clear()
    os.environ.update(env)
    try:
        spec = importlib.util.spec_from_file_location("mvmcp_under_test", LAUNCHER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, module.pin(), module.server_env()
    finally:
        os.environ.clear()
        os.environ.update(saved)


def test_local_profile_keeps_embeddings() -> None:
    _, pin, env = load({"PATH": os.environ["PATH"]})
    if "[embeddings]" not in pin:
        fail(f"the local profile must keep semantic search; pin was {pin!r}")
    if env.get("MARKDOWN_VAULT_MCP_EMBEDDING_PROVIDER") != "fastembed":
        fail(f"the local profile must pin fastembed; env was {env.get('MARKDOWN_VAULT_MCP_EMBEDDING_PROVIDER')!r}")
    if "MARKDOWN_VAULT_MCP_EMBEDDINGS_PATH" not in env:
        fail("the local profile must configure an embeddings path")
    ok("local profile keeps the [embeddings] extra and the fastembed pin")


def test_cloud_profile_drops_embeddings() -> None:
    _, pin, env = load({"PATH": os.environ["PATH"], "CLAUDE_CODE_REMOTE": "true"})
    if "[embeddings]" in pin:
        fail(
            "the cloud profile must not install the extra: fastembed's model comes "
            f"from huggingface.co, absent from the sandbox allowlist. pin was {pin!r}"
        )
    if "MARKDOWN_VAULT_MCP_EMBEDDING_PROVIDER" in env:
        fail(
            "the cloud profile must not pin a provider: the server treats an "
            "explicitly-pinned provider it cannot load as fatal, so pinning one "
            "kills the MCP at startup instead of degrading it"
        )
    if "MARKDOWN_VAULT_MCP_EMBEDDINGS_PATH" in env:
        fail("the cloud profile must not configure an embeddings path")
    ok("cloud profile drops the extra and pins no provider")


def test_cloud_profile_keeps_the_search_index() -> None:
    _, _, env = load({"PATH": os.environ["PATH"], "CLAUDE_CODE_REMOTE": "true"})
    for name in (
        "MARKDOWN_VAULT_MCP_SOURCE_DIR",
        "MARKDOWN_VAULT_MCP_INDEX_PATH",
        "MARKDOWN_VAULT_MCP_INDEXED_FIELDS",
    ):
        if name not in env:
            fail(
                f"{name} must survive the cloud profile — search, read, backlinks "
                "and outlinks rest on the FTS index and the link graph, not vectors"
            )
    ok("cloud profile keeps the FTS index configured")


def test_profile_override_wins_over_the_default() -> None:
    _, pin, env = load(
        {"PATH": os.environ["PATH"], "CLAUDE_CODE_REMOTE": "true", "MARKDOWN_VAULT_MCP_PROFILE": "full"}
    )
    if "[embeddings]" not in pin:
        fail(
            "MARKDOWN_VAULT_MCP_PROFILE=full is the documented route to full parity in "
            f"the cloud once huggingface.co is on a Custom allowlist; pin was {pin!r}"
        )
    if env.get("MARKDOWN_VAULT_MCP_EMBEDDING_PROVIDER") != "fastembed":
        fail("the override must restore the provider pin too")

    _, pin, _ = load({"PATH": os.environ["PATH"], "MARKDOWN_VAULT_MCP_PROFILE": "keyword"})
    if "[embeddings]" in pin:
        fail(f"profile=keyword must drop the extra locally too; pin was {pin!r}")
    ok("MARKDOWN_VAULT_MCP_PROFILE overrides the default in both directions")


def test_profile_change_forces_reinstall() -> None:
    """Exercise the switch, don't just read the source for it.

    An earlier version of this test asserted a substring of ensure_installed()
    and passed green while the switch crashed: uv refuses an existing venv, and
    the profile check is what made the function re-enter with one present. So
    run it — against a stub uv on PATH, since a real switch reinstalls 245 MB.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        project = tmp_path / "project"
        (project / "scripts").mkdir(parents=True)
        (project / "scripts" / "mvmcp.py").write_text(
            LAUNCHER.read_text(encoding="utf-8"), encoding="utf-8"
        )

        bindir = tmp_path / "bin"
        bindir.mkdir()
        calls = tmp_path / "calls.log"
        stub = bindir / "uv"
        stub.write_text(
            "#!/bin/bash\n"
            f'echo "$@" >> {calls}\n'
            'if [ "$1" = "venv" ]; then\n'
            # Real uv exits 2 on an existing venv unless --clear is passed.
            '  for a in "$@"; do [ "$a" = "--clear" ] && ok=1; done\n'
            '  target="${@: -1}"\n'
            '  if [ -d "$target" ] && [ -z "$ok" ]; then echo "uv: venv exists" >&2; exit 2; fi\n'
            '  mkdir -p "$target/bin"\n'
            "fi\n"
            'if [ "$1" = "pip" ]; then\n'
            '  venv=$(for a in "$@"; do echo "$a"; done | grep -m1 "/bin/python$")\n'
            '  touch "${venv%/python}/markdown-vault-mcp"\n'
            '  chmod +x "${venv%/python}/markdown-vault-mcp"\n'
            "fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        stub.chmod(0o755)
        env = {"PATH": f"{bindir}:{os.environ['PATH']}"}

        def bootstrap_install(extra_env: dict) -> None:
            spec = importlib.util.spec_from_file_location(
                "mvmcp_switch", project / "scripts" / "mvmcp.py"
            )
            module = importlib.util.module_from_spec(spec)
            saved = dict(os.environ)
            os.environ.clear()
            os.environ.update({**env, **extra_env})
            try:
                spec.loader.exec_module(module)
                module.ensure_installed()
            finally:
                os.environ.clear()
                os.environ.update(saved)

        bootstrap_install({"CLAUDE_CODE_REMOTE": "true"})
        stamp = project / ".mvmcp" / "profile"
        if "[embeddings]" in stamp.read_text(encoding="utf-8"):
            fail("the cloud profile installed the extra")

        bootstrap_install({})

        if "[embeddings]" not in stamp.read_text(encoding="utf-8"):
            fail(
                "switching cloud -> local must reinstall with the extra; the "
                f"stamp still read {stamp.read_text(encoding='utf-8').strip()!r}"
            )
        log = calls.read_text(encoding="utf-8")
        if log.count("pip install") != 2:
            fail(f"the switch must trigger a second install; uv calls were:\n{log}")

        bootstrap_install({})
        if calls.read_text(encoding="utf-8").count("pip install") != 2:
            fail("re-running on an unchanged profile must not reinstall")
    ok("a profile switch reinstalls; an unchanged profile does not")


def test_setup_script_is_pasteable_and_versioned() -> None:
    if not SETUP.exists():
        fail("scripts/cloud_setup.sh must exist for the environment's Setup script field")
    source = SETUP.read_text(encoding="utf-8")
    if "set -euo pipefail" not in source:
        fail("the setup script must fail loudly; a half-built environment gets snapshotted")
    if "mvmcp.py bootstrap" not in source:
        fail("the setup script must pre-warm the vault MCP")
    if "bun install --frozen-lockfile" not in source:
        fail("the setup script must pre-warm the frontend deps for cloud sessions (#319)")
    if "#319" not in source:
        fail("the non-fatal frontend branch must record its outcome on #319, not drop it silently")
    proc = subprocess.run(["bash", "-n", str(SETUP)], capture_output=True, text=True)
    if proc.returncode != 0:
        fail(f"scripts/cloud_setup.sh is not valid bash: {proc.stderr!r}")
    ok("cloud_setup.sh is valid, versioned, and fails loudly")


def main() -> int:
    tests = [
        test_local_profile_keeps_embeddings,
        test_cloud_profile_drops_embeddings,
        test_cloud_profile_keeps_the_search_index,
        test_profile_override_wins_over_the_default,
        test_profile_change_forces_reinstall,
        test_setup_script_is_pasteable_and_versioned,
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
