from fastapi.testclient import TestClient

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
