#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! docker info &>/dev/null; then
  echo "Start Docker Desktop first."
  exit 1
fi

docker compose up -d
echo "API:  http://localhost:8000"
echo "Run frontend: cd frontend && npm run dev → http://localhost:5173"
