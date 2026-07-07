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
    password_reset_expire_minutes: int = 15  # short-lived reset link (D23)
    skip_db_check: bool = False

    # Comma-separated allowed origins for CORS. Never "*" — the frontend sends
    # the JWT via Authorization, and credentialed requests forbid a wildcard
    # origin (ARCHITECTURE.md "Sensitive data security", middle-phases A4).
    cors_origins: str = "http://localhost:3000"

    # Public base URL of the frontend, used to build password-reset links
    # (e.g. `${frontend_url}/reset-password?token=...`). Set to the deployed
    # origin in production.
    frontend_url: str = "http://localhost:3000"

    # --- Email (password recovery, D23) ---------------------------------------
    # When email_enabled is False the app uses a console sender that logs the
    # message (dev only — never enable that path in production). Real delivery
    # uses SMTP; Gmail requires an App Password, not the account password.
    email_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from: str = ""  # falls back to smtp_user when empty

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def email_sender_address(self) -> str:
        return self.email_from or self.smtp_user


settings = Settings()
