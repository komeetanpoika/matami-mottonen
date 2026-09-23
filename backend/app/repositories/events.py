from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.capacity import Hold
from app.models import Event, Registration

_COUNTED = ("pending", "confirmed")


def holds_by_event(db: Session, event_ids: list[int]) -> dict[int, list[Hold]]:
    out: dict[int, list[Hold]] = defaultdict(list)
    if not event_ids:
        return out
    rows = db.execute(
        select(
            Registration.event_id,
            Registration.quantity,
            Registration.status,
            Registration.expires_at,
        ).where(Registration.event_id.in_(event_ids), Registration.status.in_(_COUNTED))
    )
    for event_id, quantity, status, expires_at in rows:
        out[event_id].append(Hold(quantity, status, expires_at))
    return out


def holds_for(db: Session, event_id: int) -> list[Hold]:
    return holds_by_event(db, [event_id]).get(event_id, [])


# A published event stops being publicly visible — and stops taking sign-ups —
# once it has started; `now` is passed in so callers control the clock.
def get_published_by_slug(db: Session, slug: str, now: datetime) -> Event | None:
    return db.scalar(
        select(Event).where(
            Event.slug == slug, Event.is_published.is_(True), Event.starts_at >= now
        )
    )


def lock_published_by_slug(db: Session, slug: str, now: datetime) -> Event | None:
    return db.scalar(
        select(Event)
        .where(Event.slug == slug, Event.is_published.is_(True), Event.starts_at >= now)
        .with_for_update()
    )


def list_published_upcoming(db: Session, now: datetime) -> list[Event]:
    return list(
        db.scalars(
            select(Event)
            .where(Event.is_published.is_(True), Event.starts_at >= now)
            .order_by(Event.starts_at)
        )
    )
