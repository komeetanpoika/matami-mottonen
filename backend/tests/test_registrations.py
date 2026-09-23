import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Registration
from tests.conftest import FakeStripeGateway
from tests.factories import make_event


def _pending(db: Session) -> Registration:
    ev = make_event(db, capacity=2)
    reg = Registration(
        event_id=ev.id,
        name="A",
        email="a@x.fi",
        quantity=2,
        status="pending",
        amount_cents=4000,
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
        stripe_session_id="cs_9",
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return reg


def test_status(client: TestClient, db: Session) -> None:
    reg = _pending(db)
    r = client.get(f"/api/registrations/{reg.id}/status")
    assert r.status_code == 200
    assert r.json() == {"status": "pending", "event_slug": reg.event.slug, "quantity": 2}
    assert client.get(f"/api/registrations/{uuid.uuid4()}/status").status_code == 404
    assert client.get("/api/registrations/not-a-uuid/status").status_code == 404


def test_cancel_pending_frees_seats_and_expires_stripe(
    client: TestClient, db: Session, stripe_fake: FakeStripeGateway
) -> None:
    reg = _pending(db)
    slug = reg.event.slug
    assert client.get(f"/api/events/{slug}").json()["seats_left"] == 0
    assert client.post(f"/api/registrations/{reg.id}/cancel").status_code == 204
    assert stripe_fake.expired == ["cs_9"]
    db.refresh(reg)
    assert reg.status == "expired"
    assert client.get(f"/api/events/{slug}").json()["seats_left"] == 2
    assert client.post(f"/api/registrations/{reg.id}/cancel").status_code == 409
