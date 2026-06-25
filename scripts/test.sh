#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Backend tests"
cd "$ROOT/backend"
if [ -d .venv ]; then
  . .venv/bin/activate
fi
pip install -q -r requirements.txt -r requirements-dev.txt
MONGODB_URL="${MONGODB_URL:-mongodb://localhost:27017}" \
MONGODB_DB=urbis_test \
ENVIRONMENT=test \
pytest -q

echo "==> Frontend tests"
cd "$ROOT/frontend"
npm test

echo "==> All tests passed"
