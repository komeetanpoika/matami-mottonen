import pytest

from app.config import Settings

GOOD: dict[str, object] = dict(
    env="production",
    secret_key="8f3c" * 16,
    admin_password="a-real-owner-password",
    stripe_secret_key="sk_live_realkey",
    stripe_webhook_secret="whsec_realsecret",
    # The process environment is already primed for tests by conftest, and a
    # real .env may exist beside the app; neither should reach these cases.
    _env_file=None,
)


def _settings(**overrides: object) -> Settings:
    return Settings(**{**GOOD, **overrides})  # type: ignore[arg-type]


def test_production_boots_with_real_values() -> None:
    s = _settings()
    assert s.env == "production" and s.stripe_secret_key == "sk_live_realkey"


def test_dev_tolerates_every_placeholder() -> None:
    s = Settings(env="dev", _env_file=None)  # type: ignore[call-arg]
    assert s.env == "dev"


@pytest.mark.parametrize(
    "value", ["dev-secret-change-me", "change-me-long-random", "change-me", "too-short"]
)
def test_production_rejects_placeholder_or_short_secret_key(value: str) -> None:
    with pytest.raises(RuntimeError, match="APP_SECRET_KEY"):
        _settings(secret_key=value)


@pytest.mark.parametrize("value", ["change-me", "admin", ""])
def test_production_rejects_placeholder_admin_password(value: str) -> None:
    with pytest.raises(RuntimeError, match="APP_ADMIN_PASSWORD"):
        _settings(admin_password=value)


@pytest.mark.parametrize("value", ["sk_test_placeholder", "not-a-key", ""])
def test_production_rejects_placeholder_stripe_secret_key(value: str) -> None:
    with pytest.raises(RuntimeError, match="APP_STRIPE_SECRET_KEY"):
        _settings(stripe_secret_key=value)


@pytest.mark.parametrize("value", ["whsec_placeholder", "sk_live_oops", ""])
def test_production_rejects_placeholder_webhook_secret(value: str) -> None:
    with pytest.raises(RuntimeError, match="APP_STRIPE_WEBHOOK_SECRET"):
        _settings(stripe_webhook_secret=value)
