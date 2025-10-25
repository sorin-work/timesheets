from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from the environment (or a local .env file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://timesheets:timesheets@localhost:5432/timesheets"
    secret_key: str = "change-me-in-production-0123456789abcdef"
    token_ttl_minutes: int = 60 * 24 * 7
    cors_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "info"


@lru_cache
def get_settings() -> Settings:
    return Settings()
