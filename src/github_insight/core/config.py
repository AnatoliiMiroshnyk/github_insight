"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized, typed settings.

    Secrets such as the GitHub token are read from the environment and are never
    sent to the browser. Relative paths work both from source and installed mode.
    """

    app_name: str = "GitHub Insight"
    app_version: str = "1.0.0"
    debug: bool = False
    database_url: str = "sqlite:///./data/github_insight.db"
    github_token: str | None = Field(default=None, repr=False)
    github_api_url: str = "https://api.github.com"
    cache_ttl_minutes: int = 30
    max_repository_pages: int = 3
    language_repository_limit: int = 20
    request_timeout_seconds: float = 20.0

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Return one cached settings object for the application process."""

    return Settings()


def package_dir() -> Path:
    """Return the absolute package directory used for templates/static files."""

    return Path(__file__).resolve().parents[1]
