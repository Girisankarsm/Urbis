#!/usr/bin/env bash
# Recreate API container and wait until /api/health responds.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

docker compose up -d --force-recreate api

echo "Waiting for API to start..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
    echo ""
    curl -s http://localhost:8000/api/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/api/health
    echo ""
    echo "API ready."
    exit 0
  fi
  sleep 1
done

echo "API did not become ready in 30s. Check logs:"
echo "  docker compose logs api --tail 40"
exit 1
