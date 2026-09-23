from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.slug import make_slug
from app.models import Event

OWNER = {"email": "owner@test.local", "password": "owner-pass"}


def login(client: TestClient) -> None:
    assert client.post("/api/auth/login", json=OWNER).status_code == 204


def make_event(db: Session, **overrides: object) -> Event:
    title = str(overrides.pop("title_en", "Sound Bowl Evening"))
    values: dict[str, object] = dict(
        slug=make_slug(title),
        title_en=title,
        title_fi="Äänimaljailta",
        description_en="Bring a blanket.",
        starts_at=datetime.now(UTC) + timedelta(days=1),
        location="The moss",
        price_cents=2000,
        capacity=10,
        is_published=True,
    )
    values.update(overrides)
    ev = Event(**values)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev
