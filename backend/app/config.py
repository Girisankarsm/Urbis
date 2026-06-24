from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "urbis"
    upload_dir: str = "uploads"
    api_base_url: str = "http://localhost:8000"

    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    cloudinary_folder: str = "urbis"

    lemma_token: str = ""
    lemma_pod_id: str = ""
    lemma_org_id: str = ""
    lemma_base_url: str = "https://api.lemma.work"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "urbis@demo.local"
    demo_email_to: str = "municipal-demo@example.com"
    escalation_days: int = 3
    openai_api_key: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    frontend_url: str = "http://localhost:5173"
    session_secret: str = "change-me-in-production"
    cookie_secure: bool = False

    @field_validator("cookie_secure", mode="before")
    @classmethod
    def parse_cookie_secure(cls, value: object) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes"}
        return bool(value)

    @property
    def lemma_enabled(self) -> bool:
        return bool(self.lemma_token and self.lemma_pod_id)

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


settings = Settings()
