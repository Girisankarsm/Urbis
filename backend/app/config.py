from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "civiclens"
    upload_dir: str = "uploads"
    api_base_url: str = "http://localhost:8000"

    lemma_token: str = ""
    lemma_pod_id: str = ""
    lemma_org_id: str = ""
    lemma_base_url: str = "https://api.lemma.work"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "civiclens@demo.local"
    demo_email_to: str = "municipal-demo@example.com"
    escalation_days: int = 3
    openai_api_key: str = ""

    @property
    def lemma_enabled(self) -> bool:
        return bool(self.lemma_token and self.lemma_pod_id)


settings = Settings()
