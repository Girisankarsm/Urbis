"""Lemma token resolution helpers (no network)."""

from __future__ import annotations

import asyncio
import base64
import json
import time

from app.services import lemma_service as ls


def _jwt_with_exp(exp: int) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).decode().rstrip("=")
    return f"{header}.{payload}.sig"


def test_pick_usable_token_prefers_non_expired():
    future_exp = int(time.time()) + 3600
    expired = _jwt_with_exp(future_exp - 7200)
    valid = _jwt_with_exp(future_exp)
    picked = ls._pick_usable_token(expired, valid)
    assert picked == valid


def test_token_needs_refresh_near_expiry():
    soon = int(time.time()) + 60
    token = _jwt_with_exp(soon)
    assert ls._token_needs_refresh(token) is True


def test_warm_lemma_token_does_not_force_refresh(monkeypatch):
    calls: list[bool] = []

    async def fake_resolve(*, force_refresh: bool = False) -> str:
        calls.append(force_refresh)
        return "token"

    monkeypatch.setattr(ls, "resolve_lemma_token", fake_resolve)
    monkeypatch.setattr(ls.settings, "lemma_pod_id", "pod")
    monkeypatch.setattr(ls.settings, "lemma_token", "eyJ")
    monkeypatch.setattr(ls.settings, "lemma_refresh_token", "refresh")

    asyncio.run(ls.warm_lemma_token())
    assert calls == [False]
