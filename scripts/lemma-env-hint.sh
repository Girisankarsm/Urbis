#!/usr/bin/env bash
# Print Lemma env vars for .env — run from REPO ROOT after `lemma auth login`.
#
#   cd "/path/to/Urbis"
#   backend/.venv/bin/lemma auth login
#   ./scripts/lemma-env-hint.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LEMMA="${ROOT}/backend/.venv/bin/lemma"

if [[ ! -x "$LEMMA" ]]; then
  echo "Install Lemma CLI first: cd backend && pip install -r requirements-lemma.txt"
  exit 1
fi

python3 << PY
import json
from pathlib import Path

cfg = Path.home() / ".lemma" / "config.json"
if not cfg.exists():
    raise SystemExit("No ~/.lemma/config.json — run: backend/.venv/bin/lemma auth login")

data = json.loads(cfg.read_text())
server = data.get("active_server", "default")
srv = data["servers"][server]
auth = srv.get("auth", {})
refresh = auth.get("refresh_token") or srv.get("refresh_token", "")
defaults = srv.get("defaults", {})
pod_id = defaults.get("pod_id", "")
org_id = defaults.get("org_id", "")

print("# Paste into .env (repo root) — LEMMA_TOKEN is optional (auto-refreshed):")
print(f"LEMMA_REFRESH_TOKEN={refresh}")
if pod_id:
    print(f"LEMMA_POD_ID={pod_id}")
if org_id:
    print(f"LEMMA_ORG_ID={org_id}")
print("# You can leave LEMMA_TOKEN empty after setting LEMMA_REFRESH_TOKEN.")
PY
