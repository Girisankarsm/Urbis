#!/usr/bin/env bash
# Print Lemma env vars for .env (run from repo root after `lemma auth login`).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LEMMA="${ROOT}/backend/.venv/bin/lemma"

if [[ ! -x "$LEMMA" ]]; then
  echo "Install Lemma CLI first: cd backend && pip install -r requirements-lemma.txt"
  exit 1
fi

echo "# Paste into .env:"
echo "LEMMA_TOKEN=$("$LEMMA" auth print-token)"
python3 << 'PY'
import json
from pathlib import Path
cfg = Path.home() / ".lemma" / "config.json"
if not cfg.exists():
    raise SystemExit("No ~/.lemma/config.json — run: backend/.venv/bin/lemma auth login")
data = json.loads(cfg.read_text())
server = data.get("active_server", "default")
auth = data["servers"][server].get("auth", {})
refresh = auth.get("refresh_token") or data["servers"][server].get("refresh_token", "")
print(f"LEMMA_REFRESH_TOKEN={refresh}")
PY
echo "# LEMMA_POD_ID and LEMMA_ORG_ID should already be set for your Urbis pod."
