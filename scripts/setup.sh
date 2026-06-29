#!/usr/bin/env bash
# Urbis one-time setup + start script
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Urbis setup"

# 1. Environment
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

# 2. Python 3.11 venv + dependencies
if ! command -v python3.11 &>/dev/null; then
  echo "ERROR: Python 3.11+ required. Install with: brew install python@3.11"
  exit 1
fi

if [ ! -d backend/.venv ]; then
  python3.11 -m venv backend/.venv
fi

backend/.venv/bin/pip install -q --upgrade pip
backend/.venv/bin/pip install -q -r backend/requirements.txt
backend/.venv/bin/pip install -q 'lemma-sdk==0.5.0' 'lemma-terminal==0.5.0'

echo "Python venv ready: backend/.venv (lemma-sdk 0.5.0)"

# 3. Frontend
if [ ! -d frontend/node_modules ]; then
  echo "Installing frontend dependencies..."
  (cd frontend && npm install)
else
  echo "Frontend dependencies OK"
fi

# 4. Docker (MongoDB + API)
if ! docker info &>/dev/null; then
  echo "ERROR: Docker is not running. Start Docker Desktop, then re-run: ./scripts/start.sh"
  exit 1
fi

echo "Starting MongoDB + API..."
docker compose up -d --build

echo ""
echo "==> Setup complete!"
echo ""
echo "Start the frontend:"
echo "  cd frontend && npm run dev"
echo ""
echo "Open: http://localhost:5173"
echo "API:  http://localhost:8000/api/health"
echo ""
echo "Lemma pod (when ready):"
echo "  backend/.venv/bin/lemma auth login"
echo "  backend/.venv/bin/lemma pods create civic-lens --org <org>"
echo "  backend/.venv/bin/lemma pods import ./pod/civic-lens"
