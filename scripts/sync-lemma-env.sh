#!/usr/bin/env bash
# Sync Lemma tokens from ~/.lemma/config.json into .env (repo root).
# Run after: backend/.venv/bin/lemma auth login
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 "${ROOT}/scripts/sync-lemma-env.py"
