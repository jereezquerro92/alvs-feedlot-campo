#!/usr/bin/env python3
"""Project-local launcher + bootstrap for the markdown-vault MCP (server name: markdown-vault-docs).

Transports the vendored MCP with the repo: a project-local venv under .mvmcp/.venv
and gitignored index/embeddings under .mvmcp/data/, pointed at ./docs. Nothing here
depends on a machine-global MCP registration — a fresh clone bootstraps itself on first
launch. Ruled by adr-18-markdown-vault-mcp; usage and config live in docs/markdown-vault-mcp.md.

Two profiles, because semantic search needs a model this launcher cannot always
reach. The [embeddings] extra pulls fastembed, which fetches its model from
huggingface.co on first index — a host absent from the Claude Code cloud
sandbox's Trusted allowlist. The server treats an explicitly-pinned provider it
cannot load as a fatal configuration error rather than degrading, so the full
profile does not merely lose semantic search there: the MCP never starts. The
keyword profile therefore installs no extra and pins no provider, which keeps
search, read, backlinks and outlinks alive on the FTS index and the link graph.
MARKDOWN_VAULT_MCP_PROFILE overrides the default either way;
docs/markdown-vault-mcp.md owns the profile table and the route to full parity
in the cloud.

Subcommands:
  serve      (default) bootstrap if needed, then exec the server on stdio — this is
             what .mcp.json invokes.
  bootstrap  create the venv, install the pinned server, build the index + embeddings,
             then exit. Safe to re-run.

Human output goes to stderr; stdout stays reserved for the MCP stdio JSON-RPC stream.
Any bootstrap failure surfaces on stderr with a non-zero exit.
"""

import os
import subprocess
import sys
from pathlib import Path

# Operational pin; the version policy is owned by docs/REQUIREMENTS.md.
VERSION = "3.0.4"

ROOT = Path(__file__).resolve().parents[1]
MVMCP = ROOT / ".mvmcp"
VENV = MVMCP / ".venv"
DATA = MVMCP / "data"
BIN = VENV / "bin" / "markdown-vault-mcp"
PROFILE_STAMP = MVMCP / "profile"


FULL = "full"
KEYWORD = "keyword"


def truthy(value):
    return value.strip().lower() in {"1", "true", "yes", "on"}


def profile():
    chosen = os.environ.get("MARKDOWN_VAULT_MCP_PROFILE", "").strip().lower()
    if chosen in (FULL, KEYWORD):
        return chosen
    if chosen:
        log(f"ignoring MARKDOWN_VAULT_MCP_PROFILE={chosen!r}: expected {FULL} or {KEYWORD}")
    return KEYWORD if truthy(os.environ.get("CLAUDE_CODE_REMOTE", "")) else FULL


def embeddings_enabled():
    return profile() == FULL


def pin():
    return (
        f"markdown-vault-mcp[embeddings]=={VERSION}"
        if embeddings_enabled()
        else f"markdown-vault-mcp=={VERSION}"
    )


def log(*parts):
    print("[mvmcp]", *parts, file=sys.stderr, flush=True)


def server_env():
    env = dict(os.environ)
    env.update(
        {
            "MARKDOWN_VAULT_MCP_SOURCE_DIR": str(ROOT / "docs"),
            "MARKDOWN_VAULT_MCP_READ_ONLY": "false",
            "MARKDOWN_VAULT_MCP_INDEX_PATH": str(DATA / "index.db"),
            "MARKDOWN_VAULT_MCP_STATE_PATH": str(DATA / "state.json"),
            "MARKDOWN_VAULT_MCP_EXCLUDE": ".obsidian/**,.vscode/**",
            "MARKDOWN_VAULT_MCP_INDEXED_FIELDS": "title,type,status,tags,created",
        }
    )
    if embeddings_enabled():
        env.update(
            {
                "MARKDOWN_VAULT_MCP_EMBEDDINGS_PATH": str(DATA / "embeddings"),
                "MARKDOWN_VAULT_MCP_EMBEDDING_PROVIDER": "fastembed",
                "MARKDOWN_VAULT_MCP_FASTEMBED_MODEL": "BAAI/bge-small-en-v1.5",
            }
        )
    else:
        for name in (
            "MARKDOWN_VAULT_MCP_EMBEDDINGS_PATH",
            "MARKDOWN_VAULT_MCP_EMBEDDING_PROVIDER",
        ):
            env.pop(name, None)
    return env


def installed_profile():
    try:
        return PROFILE_STAMP.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def ensure_installed():
    DATA.mkdir(parents=True, exist_ok=True)
    wanted = pin()
    if BIN.exists() and installed_profile() == wanted:
        return
    log("bootstrapping project-local venv at", VENV)
    # --clear because this runs again on a profile switch, and uv refuses an
    # existing venv otherwise. Rebuilding also guarantees the outgoing profile's
    # fastembed leaves nothing behind for auto-detection to find.
    subprocess.run(
        ["uv", "venv", "--clear", str(VENV)], check=True, stdout=sys.stderr, stderr=sys.stderr
    )
    subprocess.run(
        ["uv", "pip", "install", "--python", str(VENV / "bin" / "python"), wanted],
        check=True,
        stdout=sys.stderr,
        stderr=sys.stderr,
    )
    PROFILE_STAMP.write_text(wanted + "\n", encoding="utf-8")
    log("installed", wanted)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "serve"
    ensure_installed()
    env = server_env()
    if cmd == "bootstrap":
        subprocess.run([str(BIN), "index"], env=env, check=True, stdout=sys.stderr, stderr=sys.stderr)
        if embeddings_enabled():
            log("index + embeddings built under", DATA)
        else:
            log("index built under", DATA, "— keyword profile, semantic search off.")
            log(
                "the 'Embeddings require both ...' ValueError above is expected here:",
                "the server reports the vector step it skipped and carries on.",
                "exit 0 and an index.db under the path above are the success signal.",
            )
        return 0
    os.execve(str(BIN), [str(BIN), "serve", "--transport", "stdio"], env)


if __name__ == "__main__":
    sys.exit(main())
