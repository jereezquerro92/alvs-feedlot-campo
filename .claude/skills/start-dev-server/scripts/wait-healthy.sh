#!/usr/bin/env bash
# Wait until Django :8000 and Astro :4321 answer their health probes.
set -euo pipefail

BACKEND_URL="${BACKEND_HEALTH_URL:-http://127.0.0.1:8000/api/health/}"
FRONTEND_URL="${FRONTEND_HEALTH_URL:-http://127.0.0.1:4321/healthz}"
TIMEOUT_SEC="${WAIT_HEALTHY_TIMEOUT_SEC:-180}"
SLEEP_SEC="${WAIT_HEALTHY_SLEEP_SEC:-2}"

deadline=$((SECONDS + TIMEOUT_SEC))

probe() {
  local url="$1"
  curl -fsS --max-time 3 "$url" >/dev/null 2>&1
}

echo "wait-healthy: waiting up to ${TIMEOUT_SEC}s"
echo "  backend  ${BACKEND_URL}"
echo "  frontend ${FRONTEND_URL}"

backend_ok=0
frontend_ok=0

while (( SECONDS < deadline )); do
  if (( backend_ok == 0 )) && probe "$BACKEND_URL"; then
    echo "wait-healthy: backend OK"
    backend_ok=1
  fi
  if (( frontend_ok == 0 )) && probe "$FRONTEND_URL"; then
    echo "wait-healthy: frontend OK"
    frontend_ok=1
  fi
  if (( backend_ok == 1 && frontend_ok == 1 )); then
    echo "wait-healthy: both healthy"
    exit 0
  fi
  sleep "$SLEEP_SEC"
done

echo "wait-healthy: timed out (backend_ok=${backend_ok} frontend_ok=${frontend_ok})" >&2
exit 1
