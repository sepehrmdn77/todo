from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str
    JWT_SECRET_KEY: str
    CELERY_BROKER_URL: str = "redis://redis:6379/3"
    CELERY_BACKEND_URL: str = "redis://redis:6379/3"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
