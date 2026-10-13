from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SQLITE_URL = (
    f"sqlite:///{(Path(__file__).resolve().parents[3] / 'contract_intelligence.db').as_posix()}"
)


class Settings(BaseSettings):
    app_name: str = "Public Revenue OS"
    database_url: str = DEFAULT_SQLITE_URL
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    log_level: str = "INFO"
    environment: Literal["development", "demo", "test", "production"] = "development"
    demo_mode: bool = False
    session_cookie_name: str = "pros_session"
    csrf_cookie_name: str = "pros_csrf"
    session_cookie_secure: bool = False
    session_lifetime_hours: int = 168
    auth_rate_limit_attempts: int = 10
    auth_rate_limit_window_seconds: int = 300
    boamp_api_url: str = (
        "https://www.boamp.fr/api/explore/v2.1/catalog/datasets/boamp/records"
    )
    procurement_http_timeout_seconds: float = 20.0
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]

    def validate_runtime_safety(self) -> None:
        if self.environment == "production" and self.demo_mode:
            raise RuntimeError("DEMO_MODE must be false in production")
        if self.environment == "production" and not self.session_cookie_secure:
            raise RuntimeError("SESSION_COOKIE_SECURE must be true in production")
        if self.environment == "production" and any(
            origin == "*" or "localhost" in origin or "127.0.0.1" in origin
            for origin in self.cors_origin_list
        ):
            raise RuntimeError("Production CORS_ORIGINS must contain only explicit deployment origins")


@lru_cache
def get_settings() -> Settings:
    return Settings()
