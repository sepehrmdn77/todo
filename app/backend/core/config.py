from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Backend configuration, read from environment variables (or a local .env file)."""

    SQLALCHEMY_DATABASE_URL: str
    JWT_SECRET_KEY: str = Field(min_length=32)
    # JSON list, e.g. CORS_ORIGINS='["http://localhost:3000"]'. Empty = no cross-origin browser access.
    CORS_ORIGINS: list[str] = []

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
