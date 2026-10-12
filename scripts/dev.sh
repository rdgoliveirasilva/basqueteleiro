#!/usr/bin/env bash
# Sobe backend (8000) e frontend (5173) juntos. Ctrl+C derruba os dois.
# Execute (./scripts/dev.sh), não use `source`.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pids=()
trap 'kill "${pids[@]}" 2>/dev/null || true' EXIT INT TERM

(cd "$ROOT/backend" && exec uvicorn app.main:app --reload --port 8000) &
pids+=($!)
(cd "$ROOT/frontend" && exec npm run dev) &
pids+=($!)

echo "API: http://127.0.0.1:8000/docs   |   Site: http://localhost:5173"
wait
