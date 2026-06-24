#!/usr/bin/env bash
# Connect Urbis to Lemma cloud and import the pod bundle.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LEMMA="${ROOT}/backend/.venv/bin/lemma"

if [ ! -x "$LEMMA" ]; then
  echo "Run ./scripts/setup.sh first"
  exit 1
fi

echo "==> Lemma setup for Urbis"
echo "1. Log in to Lemma (browser opens)"
"$LEMMA" auth login

echo ""
echo "2. Create pod (skip if already exists)"
read -rp "Org ID: " ORG_ID
"$LEMMA" pods create urbis --org "$ORG_ID" || true

echo ""
echo "3. Import pod bundle"
"$LEMMA" pods import "$ROOT/pod/civic-lens"

echo ""
echo "4. Seed departments + knowledge"
"$LEMMA" records import departments "$ROOT/pod/civic-lens/seed/departments.json" || true
"$LEMMA" files upload "$ROOT/pod/civic-lens/files/knowledge/municipal-departments.md" /knowledge/municipal-departments.md || true

echo ""
echo "5. Copy these into your .env file:"
"$LEMMA" auth status 2>/dev/null || true
echo "   LEMMA_TOKEN=<from lemma auth>"
echo "   LEMMA_POD_ID=<your pod id>"
echo "   LEMMA_ORG_ID=$ORG_ID"
echo ""
echo "Then: docker compose restart api"
