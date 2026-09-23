from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db import get_db
from app.domain.capacity import Hold, seats_left, seats_taken
from app.domain.slug import make_slug
from app.models import Event, Registration
from app.repositories.events import holds_by_event
from app.schemas import AdminEventOut, EventIn

router = APIRouter(prefix="/admin/events", tags=["admin"], dependencies=[Depends(require_admin)])


def admin_out(ev: Event, holds: list[Hold], now: datetime) -> AdminEventOut:
    confirmed = sum(h.quantity for h in holds if h.status == "confirmed")
    pending = seats_taken(holds, now) - confirmed
    left = seats_left(ev.capacity, holds, now)
    return AdminEventOut(
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
        is_published=ev.is_published,
        confirmed_count=confirmed,
        pending_count=pending,
    )


def _apply(ev: Event, body: EventIn) -> None:
    for field, value in body.model_dump().items():
        setattr(ev, field, value)


@router.get("", response_model=list[AdminEventOut])
def list_events(db: Session = Depends(get_db)) -> list[AdminEventOut]:
    now = datetime.now(UTC)
    events = list(db.scalars(select(Event).order_by(Event.starts_at.desc())))
    holds = holds_by_event(db, [e.id for e in events])
    return [admin_out(e, holds.get(e.id, []), now) for e in events]


@router.post("", response_model=AdminEventOut, status_code=201)
def create_event(body: EventIn, db: Session = Depends(get_db)) -> AdminEventOut:
    ev = Event(slug=make_slug(body.title_en or body.title_fi or "event"), currency="EUR")
    _apply(ev, body)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return admin_out(ev, [], datetime.now(UTC))


def _get(db: Session, event_id: int) -> Event:
    ev = db.get(Event, event_id)
    if ev is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return ev


@router.get("/{event_id}", response_model=AdminEventOut)
def get_event(event_id: int, db: Session = Depends(get_db)) -> AdminEventOut:
    ev = _get(db, event_id)
    return admin_out(ev, holds_by_event(db, [ev.id]).get(ev.id, []), datetime.now(UTC))


@router.put("/{event_id}", response_model=AdminEventOut)
def update_event(event_id: int, body: EventIn, db: Session = Depends(get_db)) -> AdminEventOut:
    ev = _get(db, event_id)
    _apply(ev, body)
    db.commit()
    db.refresh(ev)
    return admin_out(ev, holds_by_event(db, [ev.id]).get(ev.id, []), datetime.now(UTC))


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)) -> None:
    ev = _get(db, event_id)
    now = datetime.now(UTC)
    regs = list(db.scalars(select(Registration).where(Registration.event_id == ev.id)))
    # `confirmed` and `cancelled` rows are the refund trail and must survive;
    # a live `pending` row is a paid-or-about-to-be-paid Stripe session whose
    # webhook would land on a deleted event.
    if any(
        r.status in ("confirmed", "cancelled") or (r.status == "pending" and r.expires_at > now)
        for r in regs
    ):
        raise HTTPException(status_code=409, detail="Event has registrations")
    # Only dead holds are left; they go first because of ondelete=RESTRICT.
    for reg in regs:
        db.delete(reg)
    db.delete(ev)
    db.commit()
