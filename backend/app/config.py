from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env")

    env: Literal["dev", "test", "production"] = "dev"
    database_url: str = "postgresql+psycopg://fish:fish@localhost:5433/matami"
    secret_key: str = _DEV_SECRET
    session_ttl_hours: int = 336  # 14 days
    login_rate_limit: int = 5  # attempts / 5 min per IP
    public_base_url: str = "http://localhost:5173"
    admin_email: str = "admin@example.com"
    admin_password: str = "admin"
    stripe_secret_key: str = "sk_test_placeholder"
    stripe_webhook_secret: str = "whsec_placeholder"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "matami@example.com"
    contact_email: str = "matami@example.com"
    hold_minutes: int = 31
    sweep_interval_seconds: int = 300

    def model_post_init(self, _context: object) -> None:
        if self.env == "production" and self.secret_key == _DEV_SECRET:
            raise RuntimeError("APP_SECRET_KEY must be set in production")


settings = Settings()
