from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ucuncugoz"
    aws_region: str = "eu-central-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    s3_bucket: str = "ucuncugoz-videos"
    rekognition_min_confidence: float = 70.0
    rekognition_role_arn: str | None = None
    cors_origins: str = "http://localhost:3000"


settings = Settings()
