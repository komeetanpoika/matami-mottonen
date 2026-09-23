from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.capacity import Hold, seats_left
from app.models import Event
from app.repositories.events import get_published_by_slug, holds_by_event, list_published_upcoming
from app.schemas import EventOut

router = APIRouter(prefix="/events", tags=["events"])


def public_out(ev: Event, holds: list[Hold], now: datetime) -> EventOut:
    left = seats_left(ev.capacity, holds, now)
    return EventOut(
        id=ev.id,
        slug=ev.slug,
        title_fi=ev.title_fi,
        title_en=ev.title_en,
        description_fi=ev.description_fi,
        description_en=ev.description_en,
        starts_at=ev.starts_at,
        ends_at=ev.ends_at,
        location=ev.location,
        price_cents=ev.price_cents,
        currency=ev.currency,
        capacity=ev.capacity,
        seats_left=left,
        sold_out=left == 0,
    )


@router.get("", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)) -> list[EventOut]:
    now = datetime.now(UTC)
    events = list_published_upcoming(db, now)
    holds = holds_by_event(db, [e.id for e in events])
    return [public_out(e, holds.get(e.id, []), now) for e in events]


@router.get("/{slug}", response_model=EventOut)
def get_event(slug: str, db: Session = Depends(get_db)) -> EventOut:
    ev = get_published_by_slug(db, slug)
    if ev is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return public_out(ev, holds_by_event(db, [ev.id]).get(ev.id, []), datetime.now(UTC))
