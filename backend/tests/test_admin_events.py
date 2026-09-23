from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Event, Registration
from tests.factories import login, make_event

BODY = {
    "title_fi": "Tarot-ilta",
    "title_en": "Tarot Night",
    "description_fi": None,
    "description_en": "Cards.",
    "starts_at": "2026-10-10T16:00:00Z",
    "ends_at": None,
    "location": "Forest",
    "price_cents": 1500,
    "capacity": 8,
    "is_published": False,
}


def test_admin_routes_require_login(client: TestClient) -> None:
    assert client.get("/api/admin/events").status_code == 401
    assert client.post("/api/admin/events", json=BODY).status_code == 401


def test_create_list_update_delete(client: TestClient, db: Session) -> None:
    login(client)
    r = client.post("/api/admin/events", json=BODY)
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["slug"].startswith("tarot-night-")
    assert created["confirmed_count"] == 0 and created["pending_count"] == 0

    r = client.get("/api/admin/events")
    assert [e["id"] for e in r.json()] == [created["id"]]

    r = client.put(
        f"/api/admin/events/{created['id']}", json={**BODY, "capacity": 12, "is_published": True}
    )
    assert r.status_code == 200 and r.json()["capacity"] == 12 and r.json()["is_published"] is True
    assert r.json()["slug"] == created["slug"]  # slug is immutable

    assert client.delete(f"/api/admin/events/{created['id']}").status_code == 204
    assert client.get("/api/admin/events").json() == []


def test_create_requires_a_title(client: TestClient) -> None:
    login(client)
    r = client.post("/api/admin/events", json={**BODY, "title_fi": None, "title_en": None})
    assert r.status_code == 422


def test_counts_and_delete_guard(client: TestClient, db: Session) -> None:
    login(client)
    ev = make_event(db)
    now = datetime.now(UTC)
    db.add_all(
        [
            Registration(
                event_id=ev.id,
                name="A",
                email="a@x.fi",
                quantity=2,
                status="confirmed",
                amount_cents=4000,
                expires_at=now,
                confirmed_at=now,
            ),
            Registration(
                event_id=ev.id,
                name="B",
                email="b@x.fi",
                quantity=1,
                status="pending",
                amount_cents=2000,
                expires_at=now + timedelta(minutes=30),
            ),
            Registration(
                event_id=ev.id,
                name="C",
                email="c@x.fi",
                quantity=1,
                status="pending",
                amount_cents=2000,
                expires_at=now - timedelta(minutes=1),
            ),
        ]
    )
    db.commit()
    row = client.get("/api/admin/events").json()[0]
    assert row["confirmed_count"] == 2 and row["pending_count"] == 1
    assert client.delete(f"/api/admin/events/{ev.id}").status_code == 409
    assert db.get(Event, ev.id) is not None


def test_delete_blocked_by_a_live_pending_hold(client: TestClient, db: Session) -> None:
    login(client)
    ev = make_event(db)
    now = datetime.now(UTC)
    db.add(
        Registration(
            event_id=ev.id,
            name="B",
            email="b@x.fi",
            quantity=1,
            status="pending",
            amount_cents=2000,
            expires_at=now + timedelta(minutes=30),
        )
    )
    db.commit()
    assert client.delete(f"/api/admin/events/{ev.id}").status_code == 409
    assert db.get(Event, ev.id) is not None


def test_delete_blocked_by_a_cancelled_registration(client: TestClient, db: Session) -> None:
    login(client)
    ev = make_event(db)
    now = datetime.now(UTC)
    db.add(
        Registration(
            event_id=ev.id,
            name="C",
            email="c@x.fi",
            quantity=1,
            status="cancelled",
            amount_cents=2000,
            expires_at=now,
        )
    )
    db.commit()
    assert client.delete(f"/api/admin/events/{ev.id}").status_code == 409


def test_delete_clears_dead_holds(client: TestClient, db: Session) -> None:
    login(client)
    ev = make_event(db)
    now = datetime.now(UTC)
    db.add_all(
        [
            Registration(
                event_id=ev.id,
                name="D",
                email="d@x.fi",
                quantity=1,
                status="expired",
                amount_cents=2000,
                expires_at=now - timedelta(hours=1),
            ),
            Registration(
                event_id=ev.id,
                name="E",
                email="e@x.fi",
                quantity=1,
                status="pending",
                amount_cents=2000,
                expires_at=now - timedelta(minutes=1),
            ),
        ]
    )
    db.commit()
    event_id = ev.id
    assert client.delete(f"/api/admin/events/{event_id}").status_code == 204
    db.expire_all()
    assert db.get(Event, event_id) is None
    assert db.scalar(select(func.count()).select_from(Registration)) == 0
