#!/bin/bash
# Cloud environment setup script for a Claude Code cloud session.
#
# Paste this one line into the environment's "Setup script" field:
#
#     bash scripts/cloud_setup.sh
#
# Everything else stays versioned here. The script runs once per environment,
# before Claude Code launches; Anthropic snapshots the filesystem afterwards, so
# later sessions start with the work already on disk. Keep it well under the
# ~5 minute budget or the snapshot never builds and every session pays the cost.
#
# Configuration and the profile table: docs/markdown-vault-mcp.md. Force: adr-18.
set -euo pipefail

echo "[cloud_setup] pre-warming the markdown-vault MCP"

# The launcher reads CLAUDE_CODE_REMOTE to pick its profile. The setup script
# runs before Claude Code launches, so the variable is not set for us yet —
# state the intent outright rather than depend on ambient environment. Set
# this to 'full' in the environment (with huggingface.co on a Custom
# allowlist) to get semantic search here too.
export MARKDOWN_VAULT_MCP_PROFILE="${MARKDOWN_VAULT_MCP_PROFILE:-keyword}"

python3 scripts/mvmcp.py bootstrap

echo "[cloud_setup] done — vault MCP ready, profile: $(cat .mvmcp/profile)"

echo "[cloud_setup] pre-warming the frontend dependencies (bun install)"

# Bake node_modules into the environment snapshot so a cloud session can build
# the frontend, not only propose the change (#319). This is bun-only with
# --frozen-lockfile, matching frontend/Dockerfile and ci.yml — npm is prohibited
# and Node is not in the stack (adr-04 rule 2).
#
# Deliberately NON-FATAL, unlike the MCP bootstrap above. A missing node_modules
# is graceful degradation (the session can still install, or use the oven/bun
# Docker path), not a half-built environment — so a proxy failure/hang here must
# never abort setup or cost the MCP snapshot. The if/subshell keeps set -e from
# aborting; the script still exits 0 so the snapshot builds either way. A failure
# is a signal to record works/partial/fails on #319, not a reason to lose the MCP.
if command -v bun >/dev/null 2>&1; then
    if (cd frontend && timeout 180 bun install --frozen-lockfile); then
        echo "[cloud_setup] frontend deps installed — node_modules baked into snapshot"
    else
        echo "[cloud_setup] WARNING: bun install failed or timed out behind the sandbox proxy — record works/partial/fails on #319" >&2
    fi
else
    echo "[cloud_setup] WARNING: bun not found in this environment — cannot pre-warm frontend deps (record on #319)" >&2
fi
