#!/usr/bin/env bash
# Run Urbis locally without Docker (MongoDB must already be running).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

MONGODB_URL="${MONGODB_URL:-mongodb://localhost:27017}"
if [[ "$MONGODB_URL" == mongodb://localhost* ]] || [[ "$MONGODB_URL" == mongodb://127.0.0.1* ]]; then
  if ! mongosh --eval "db.runCommand({ ping: 1 })" --quiet >/dev/null 2>&1; then
    echo "MongoDB is not running. Start it first, or set MONGODB_URL in .env to Atlas."
    exit 1
  fi
fi

echo "Starting API on http://localhost:8000 (MONGODB_URL from .env) ..."
(cd "$ROOT/backend" && .venv/bin/uvicorn app.main:app --reload --port 8000) &
API_PID=$!

cleanup() {
  kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT

sleep 2
echo "Starting frontend on http://localhost:5173 ..."
cd "$ROOT/frontend" && npm run dev
