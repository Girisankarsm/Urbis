#!/usr/bin/env bash
# Seed departments table after pod import.
# Usage: lemma records import departments ./seed/departments.json

set -euo pipefail

echo "Seed departments via: lemma records import departments ./seed/departments.json"
echo "Upload knowledge: lemma files upload ./files/knowledge/municipal-departments.md /knowledge/municipal-departments.md"
