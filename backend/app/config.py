from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ucuncugoz"

    # Google Cloud
    gcp_project: str | None = None
    gcs_bucket: str = "ucuncugoz-videos"
    # Optional: path to a service account JSON key for local development.
    # On Cloud Run this is unused — the runtime service account is picked up
    # automatically by google.auth.default().
    google_application_credentials: str | None = None

    # Video Intelligence
    video_intelligence_min_confidence: float = 0.6

    # CORS
    cors_origins: str = "http://localhost:3000"


settings = Settings()
