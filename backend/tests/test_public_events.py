from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Registration
from tests.factories import make_event


def test_list_only_published_upcoming_sorted(client: TestClient, db: Session) -> None:
    now = datetime.now(UTC)
    later = make_event(db, title_en="Later", starts_at=now + timedelta(days=5))
    soon = make_event(db, title_en="Soon", starts_at=now + timedelta(days=1))
    make_event(db, title_en="Past", starts_at=now - timedelta(days=1))
    make_event(db, title_en="Draft", is_published=False)
    slugs = [e["slug"] for e in client.get("/api/events").json()]
    assert slugs == [soon.slug, later.slug]


def test_detail_has_seats_left_and_hides_drafts(client: TestClient, db: Session) -> None:
    ev = make_event(db, capacity=5)
    draft = make_event(db, is_published=False)
    now = datetime.now(UTC)
    db.add(
        Registration(
            event_id=ev.id,
            name="A",
            email="a@x.fi",
            quantity=2,
            status="confirmed",
            amount_cents=4000,
            expires_at=now,
            confirmed_at=now,
        )
    )
    db.add(
        Registration(
            event_id=ev.id,
            name="B",
            email="b@x.fi",
            quantity=3,
            status="expired",
            amount_cents=6000,
            expires_at=now,
        )
    )
    db.commit()
    body = client.get(f"/api/events/{ev.slug}").json()
    assert body["seats_left"] == 3 and body["sold_out"] is False
    assert "is_published" not in body
    assert client.get(f"/api/events/{draft.slug}").status_code == 404
    assert client.get("/api/events/nope").status_code == 404


def test_detail_404_for_a_past_event(client: TestClient, db: Session) -> None:
    past = make_event(db, title_en="Past", starts_at=datetime.now(UTC) - timedelta(minutes=1))
    assert client.get(f"/api/events/{past.slug}").status_code == 404


def test_sold_out_flag(client: TestClient, db: Session) -> None:
    ev = make_event(db, capacity=1)
    now = datetime.now(UTC)
    db.add(
        Registration(
            event_id=ev.id,
            name="A",
            email="a@x.fi",
            quantity=1,
            status="pending",
            amount_cents=2000,
            expires_at=now + timedelta(minutes=20),
        )
    )
    db.commit()
    body = client.get(f"/api/events/{ev.slug}").json()
    assert body["seats_left"] == 0 and body["sold_out"] is True
