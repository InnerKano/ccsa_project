"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://postgres:postgres@localhost:5432/ccsa"
    environment: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days
    skip_db_check: bool = False

    # Comma-separated allowed origins for CORS. Never "*" — the frontend sends
    # the JWT via Authorization, and credentialed requests forbid a wildcard
    # origin (ARCHITECTURE.md "Sensitive data security", middle-phases A4).
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
