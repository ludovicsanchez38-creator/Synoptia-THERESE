#!/usr/bin/env bash
# Backend E2E jetable (revue 0.40) : port dédié + THERESE_DATA_DIR temporaire,
# détruit en fin de suite. Lancé par le webServer de playwright.config.ts.
set -euo pipefail

PORT="${THERESE_E2E_PORT:-17393}"
if [ "$PORT" = "17293" ]; then
  echo "E2E interdits sur le port 17293 (instance THÉRÈSE réelle)" >&2
  exit 1
fi

# Data dir DÉTERMINISTE par port : purgé ici à chaque départ, détruit en fin
# de suite par le globalTeardown Playwright (le SIGKILL de Playwright sur ce
# shell court-circuite le trap - le teardown Node, lui, s'exécute toujours).
DATA_DIR="${TMPDIR:-/tmp}/therese-e2e-$PORT"
rm -rf "$DATA_DIR"
mkdir -p "$DATA_DIR"
export THERESE_DATA_DIR="$DATA_DIR"

cleanup() {
  if [ -n "${UVICORN_PID:-}" ]; then
    kill "$UVICORN_PID" 2>/dev/null || true
    wait "$UVICORN_PID" 2>/dev/null || true
  fi
  rm -rf "$DATA_DIR"
}
# PAS de `exec` : le shell doit survivre à uvicorn pour exécuter ce trap.
trap cleanup EXIT INT TERM

cd "$(dirname "$0")/../.."
echo "[e2e-backend] port $PORT, données jetables : $DATA_DIR"
uv run uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --app-dir src/backend &
UVICORN_PID=$!
wait "$UVICORN_PID"
