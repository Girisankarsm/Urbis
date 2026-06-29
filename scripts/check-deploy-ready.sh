#!/usr/bin/env bash
# Validate production configuration before deploying.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

export ENVIRONMENT="${ENVIRONMENT:-production}"
export MONGODB_URL="${MONGODB_URL:-mongodb://localhost:27017}"

.venv/bin/python - <<'PY'
import os
import sys

# Simulate production check; override with real env vars when set.
from app.config import settings
from app.deploy_checks import validate_deploy_config

errors, warnings = validate_deploy_config()

print(f"Environment: {settings.environment}")
print(f"API base:    {settings.api_base_url}")
print(f"Frontend:    {settings.frontend_url}")
print(f"MongoDB:     {settings.mongodb_url[:40]}...")
print(f"Lemma:       {'enabled' if settings.lemma_enabled else 'disabled'}")
print(f"Cloudinary:  {'yes' if settings.cloudinary_enabled else 'no'}")
print(f"Google auth: {'yes' if settings.google_auth_enabled else 'no'}")
print()

for w in warnings:
    print(f"WARN: {w}")
for e in errors:
    print(f"ERROR: {e}")

if errors:
    print()
    print("Fix errors above before deploying. See docs/DEPLOY.md")
    sys.exit(1)

if warnings:
    print()
    print("Warnings only — deploy can proceed but review docs/DEPLOY.md")
else:
    print()
    print("Production configuration looks good.")
PY
