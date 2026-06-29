#!/usr/bin/env bash
# Run Urbis locally without Docker (MongoDB must already be running).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if ! mongosh --eval "db.runCommand({ ping: 1 })" --quiet >/dev/null 2>&1; then
  echo "MongoDB is not running. Start it first, or use: ./scripts/start.sh (Docker)"
  exit 1
fi

echo "Starting API on http://localhost:8000 ..."
(cd "$ROOT/backend" && MONGODB_URL="${MONGODB_URL:-mongodb://localhost:27017}" .venv/bin/uvicorn app.main:app --reload --port 8000) &
API_PID=$!

cleanup() {
  kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT

sleep 2
echo "Starting frontend on http://localhost:5173 ..."
cd "$ROOT/frontend" && npm run dev
