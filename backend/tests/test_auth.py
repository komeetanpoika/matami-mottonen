from fastapi.testclient import TestClient

from app.api import auth as auth_module
from app.api.rate_limit import SlidingWindowLimiter
from app.config import settings

LOGIN = {"email": "owner@test.local", "password": "owner-pass"}


def test_me_requires_login(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_login_sets_cookie_and_me_works(client: TestClient) -> None:
    r = client.post("/api/auth/login", json=LOGIN)
    assert r.status_code == 204
    assert "mm_session" in r.cookies
    assert client.get("/api/auth/me").json() == {"email": "owner@test.local"}


def test_wrong_password_401(client: TestClient) -> None:
    r = client.post("/api/auth/login", json={**LOGIN, "password": "nope"})
    assert r.status_code == 401


def test_logout_clears_session(client: TestClient) -> None:
    client.post("/api/auth/login", json=LOGIN)
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_login_rate_limited(client: TestClient) -> None:
    for _ in range(5):
        client.post("/api/auth/login", json={**LOGIN, "password": "nope"})
    assert client.post("/api/auth/login", json=LOGIN).status_code == 429


def test_tampered_cookie_rejected(client: TestClient) -> None:
    client.cookies.set("mm_session", "garbage.value")
    assert client.get("/api/auth/me").status_code == 401


def test_login_rate_limited_per_account_across_ips(client: TestClient) -> None:
    for _ in range(5):
        assert client.post("/api/auth/login", json={**LOGIN, "password": "nope"}).status_code == 401
    # TestClient always reports the same client IP, so an attacker rotating IPs
    # is simulated by handing the per-IP limiter a clean window. The per-account
    # window is untouched and must still refuse the sixth attempt.
    auth_module._ip_limiter = SlidingWindowLimiter(settings.login_rate_limit, 300)
    assert client.post("/api/auth/login", json=LOGIN).status_code == 429


def test_account_limit_keys_on_the_normalised_email(client: TestClient) -> None:
    for _ in range(5):
        client.post("/api/auth/login", json={"email": " OWNER@Test.Local ", "password": "nope"})
    auth_module._ip_limiter = SlidingWindowLimiter(settings.login_rate_limit, 300)
    assert client.post("/api/auth/login", json=LOGIN).status_code == 429


def test_login_email_over_max_length_is_422(client: TestClient) -> None:
    long_email = ("a" * 310) + "@test.local"  # > 320 chars
    r = client.post("/api/auth/login", json={"email": long_email, "password": "x"})
    assert r.status_code == 422


def test_successful_login_clears_the_account_window(client: TestClient) -> None:
    # Three successful logins would already exceed the account window if
    # success counted toward it; resetting the IP limiter between them
    # isolates the account window as the thing under test.
    for _ in range(3):
        auth_module._ip_limiter = SlidingWindowLimiter(settings.login_rate_limit, 300)
        assert client.post("/api/auth/login", json=LOGIN).status_code == 204

    auth_module._ip_limiter = SlidingWindowLimiter(settings.login_rate_limit, 300)
    for _ in range(5):
        r = client.post("/api/auth/login", json={**LOGIN, "password": "nope"})
        assert r.status_code == 401

    # A fresh IP budget isolates the account window: the 6th failure alone
    # trips it, proving only failures were ever counted.
    auth_module._ip_limiter = SlidingWindowLimiter(settings.login_rate_limit, 300)
    assert client.post("/api/auth/login", json={**LOGIN, "password": "nope"}).status_code == 429
