from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    port: int = 8000
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "urbis"
    upload_dir: str = "uploads"
    api_base_url: str = "http://localhost:8000"
    cors_origins: str = ""

    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    cloudinary_folder: str = "urbis"

    lemma_token: str = ""
    lemma_refresh_token: str = ""
    lemma_pod_id: str = ""
    lemma_org_id: str = ""
    lemma_base_url: str = "https://api.lemma.work"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "urbis@demo.local"
    demo_email_to: str = "municipal-demo@example.com"
    demo_email_redirect: bool = False
    authority_discovery_enabled: bool = True
    authority_discovery_timeout_seconds: int = 15
    lemma_agent_timeout_seconds: int = 25
    lemma_pipeline_timeout_seconds: int = 8
    escalation_days: int = 3
    openai_api_key: str = ""
    vision_model: str = "gpt-4o-mini"
    vision_timeout_seconds: int = 30
    vision_enabled: bool = True
    severity_poi_radius_m: int = 500
    infrastructure_radius_m: int | None = None
    infrastructure_alpha: float | None = None
    duplicate_radius_m: float = 500.0
    upload_max_bytes: int = 10 * 1024 * 1024
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 120

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    frontend_url: str = "http://localhost:5173"
    session_secret: str = "change-me-in-production"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    @field_validator("cookie_secure", mode="before")
    @classmethod
    def parse_cookie_secure(cls, value: object) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes"}
        return bool(value)

    @field_validator("cookie_samesite", mode="before")
    @classmethod
    def normalize_samesite(cls, value: object) -> str:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"lax", "strict", "none"}:
                return normalized
        return "lax"

    @field_validator("demo_email_redirect", mode="before")
    @classmethod
    def parse_demo_email_redirect(cls, value: object) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes"}
        return bool(value)

    @field_validator("vision_enabled", "rate_limit_enabled", mode="before")
    @classmethod
    def parse_bool_flags(cls, value: object) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes"}
        if value is None:
            return True
        return bool(value)

    @field_validator("authority_discovery_enabled", mode="before")
    @classmethod
    def parse_authority_discovery_enabled(cls, value: object) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes"}
        if value is None:
            return True
        return bool(value)

    @property
    def lemma_enabled(self) -> bool:
        return bool(
            self.lemma_pod_id
            and (self.lemma_token or self.lemma_refresh_token)
        )

    @property
    def google_auth_enabled(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def cloudinary_enabled(self) -> bool:
        return bool(
            self.cloudinary_cloud_name
            and self.cloudinary_api_key
            and self.cloudinary_api_secret
        )

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        origins = {
            self.frontend_url.rstrip("/"),
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        }
        if self.cors_origins:
            for origin in self.cors_origins.split(","):
                cleaned = origin.strip().rstrip("/")
                if cleaned:
                    origins.add(cleaned)
        return sorted(origins)

    @property
    def effective_cookie_secure(self) -> bool:
        return self.cookie_secure or self.is_production

    @property
    def effective_cookie_samesite(self) -> str:
        if self.is_production and self.cookie_samesite == "lax":
            return "none"
        return self.cookie_samesite

    @property
    def use_demo_email_redirect(self) -> bool:
        """In development, send to DEMO_EMAIL_TO so citizens can verify delivery."""
        if self.is_production:
            return False
        if not self.demo_email_redirect:
            return False
        return bool(self.demo_email_to and self.demo_email_to != "municipal-demo@example.com")


settings = Settings()
