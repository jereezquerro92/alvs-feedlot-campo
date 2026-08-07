#!/usr/bin/env bash
# Free host listeners on 8000 and 4321 — any process, any project.
# Safe to run when nothing is bound.
set -euo pipefail

PORTS=(8000 4321)

free_port() {
  local port="$1"
  local pids=""

  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -t -iTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
  elif command -v fuser >/dev/null 2>&1; then
    # fuser prints PIDs to stderr; normalize
    pids="$(fuser "${port}/tcp" 2>/dev/null || true)"
  elif command -v ss >/dev/null 2>&1; then
    pids="$(
      ss -lptn "sport = :${port}" 2>/dev/null \
        | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' \
        | sort -u || true
    )"
  else
    echo "free-ports: need lsof, fuser, or ss" >&2
    exit 1
  fi

  if [[ -z "${pids// /}" ]]; then
    echo "free-ports: :${port} — nothing listening"
    return 0
  fi

  echo "free-ports: :${port} — killing PIDs: ${pids}"
  # shellcheck disable=SC2086
  kill ${pids} 2>/dev/null || true
  sleep 0.5
  # shellcheck disable=SC2086
  kill -9 ${pids} 2>/dev/null || true
}

for p in "${PORTS[@]}"; do
  free_port "$p"
done

echo "free-ports: done"
