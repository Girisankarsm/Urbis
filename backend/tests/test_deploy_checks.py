"""Production deploy configuration validation."""

from app.config import settings
from app.deploy_checks import validate_deploy_config


def test_production_rejects_localhost_mongo(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "mongodb_url", "mongodb://localhost:27017")
    monkeypatch.setattr(settings, "session_secret", "x" * 32)
    monkeypatch.setattr(settings, "frontend_url", "https://app.example.com")
    monkeypatch.setattr(settings, "api_base_url", "https://api.example.com")
    monkeypatch.setattr(settings, "google_client_id", "")
    monkeypatch.setattr(settings, "google_client_secret", "")

    errors, _ = validate_deploy_config()
    assert any("MONGODB_URL" in e for e in errors)


def test_development_allows_localhost(monkeypatch):
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "mongodb_url", "mongodb://localhost:27017")

    errors, _ = validate_deploy_config()
    assert not errors
