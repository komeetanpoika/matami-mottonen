from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "dev-secret-change-me"
_PLACEHOLDER_SECRETS = {_DEV_SECRET, "change-me-long-random", "change-me"}
_PLACEHOLDER_PASSWORDS = {"change-me", "admin", ""}
_PLACEHOLDER_STRIPE_KEY = "sk_test_placeholder"
_PLACEHOLDER_WEBHOOK_SECRET = "whsec_placeholder"


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
    # Stripe requires a Checkout Session's expires_at to be at least 30 minutes
    # after creation, so the hold must outlast that floor plus some margin.
    hold_minutes: int = Field(default=31, ge=31)
    sweep_interval_seconds: int = 300

    def model_post_init(self, _context: object) -> None:
        """Refuse to boot production on a value straight out of .env.example."""
        if self.env != "production":
            return
        if self.secret_key in _PLACEHOLDER_SECRETS or len(self.secret_key) < 32:
            raise RuntimeError(
                "APP_SECRET_KEY must be a real secret of at least 32 characters in production"
                " (openssl rand -hex 32)"
            )
        if self.admin_password in _PLACEHOLDER_PASSWORDS:
            raise RuntimeError("APP_ADMIN_PASSWORD must be set to a real password in production")
        if (
            not self.stripe_secret_key.startswith("sk_")
            or self.stripe_secret_key == _PLACEHOLDER_STRIPE_KEY
        ):
            raise RuntimeError("APP_STRIPE_SECRET_KEY must be a real sk_… key in production")
        if (
            not self.stripe_webhook_secret.startswith("whsec_")
            or self.stripe_webhook_secret == _PLACEHOLDER_WEBHOOK_SECRET
        ):
            raise RuntimeError(
                "APP_STRIPE_WEBHOOK_SECRET must be a real whsec_… secret in production"
            )


settings = Settings()
