from fastapi import HTTPException

import pytest

from app.config import settings
from app.services.access import assert_petition_access


def test_assert_petition_access_allows_owner(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "id")
    monkeypatch.setattr(settings, "google_client_secret", "secret")
    assert_petition_access({"reporter_user_id": "u1"}, {"_id": "u1"})


def test_assert_petition_access_blocks_other_user(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "id")
    monkeypatch.setattr(settings, "google_client_secret", "secret")
    with pytest.raises(HTTPException) as exc:
        assert_petition_access({"reporter_user_id": "u2"}, {"_id": "u1"})
    assert exc.value.status_code == 403


def test_assert_petition_access_skipped_in_demo_mode(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "")
    monkeypatch.setattr(settings, "google_client_secret", "")
    assert_petition_access({"reporter_user_id": "u2"}, None)
