#!/usr/bin/env python3
"""Sync LEMMA_* vars from ~/.lemma/config.json into project .env."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
CFG_PATH = Path.home() / ".lemma" / "config.json"


def set_var(text: str, name: str, value: str) -> str:
    pattern = rf"^{re.escape(name)}=.*$"
    line = f"{name}={value}"
    if re.search(pattern, text, flags=re.M):
        return re.sub(pattern, line, text, flags=re.M)
    return text.rstrip() + f"\n{line}\n"


def main() -> int:
    if not CFG_PATH.is_file():
        print("No ~/.lemma/config.json — run: backend/.venv/bin/lemma auth login", file=sys.stderr)
        return 1
    if not ENV_PATH.is_file():
        print("No .env file found in repo root", file=sys.stderr)
        return 1

    data = json.loads(CFG_PATH.read_text())
    server = data.get("active_server", "default")
    srv = data["servers"][server]
    auth = srv.get("auth", {})
    refresh = auth.get("refresh_token") or srv.get("refresh_token", "")
    access = auth.get("access_token") or srv.get("token", "")
    defaults = srv.get("defaults", {})
    pod_id = defaults.get("pod_id", "")
    org_id = defaults.get("org_id", "")

    if not refresh:
        print("No refresh_token in Lemma CLI config", file=sys.stderr)
        return 1

    text = ENV_PATH.read_text()
    text = set_var(text, "LEMMA_REFRESH_TOKEN", refresh)
    # Drop stale access token — API auto-refreshes from LEMMA_REFRESH_TOKEN.
    text = re.sub(r"^LEMMA_TOKEN=.*\n", "", text, flags=re.M)
    if pod_id:
        text = set_var(text, "LEMMA_POD_ID", pod_id)
    if org_id:
        text = set_var(text, "LEMMA_ORG_ID", org_id)
    ENV_PATH.write_text(text)
    print("Updated .env: LEMMA_REFRESH_TOKEN, LEMMA_POD_ID, LEMMA_ORG_ID (removed LEMMA_TOKEN)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
