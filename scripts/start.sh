#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! docker info &>/dev/null; then
  echo "Start Docker Desktop first."
  exit 1
fi

docker compose up -d
echo "Waiting for API health check..."
for _ in $(seq 1 30); do
  if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
curl -sf http://localhost:8000/api/health || {
  echo "API not ready — check: docker compose logs api --tail 30"
  exit 1
}
echo ""
echo "API:  http://localhost:8000"
echo "Run frontend: cd frontend && npm run dev → http://localhost:5173"
