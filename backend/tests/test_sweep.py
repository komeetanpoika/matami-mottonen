from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Registration
from app.services.sweep import expire_stale_holds
from tests.factories import make_event


def test_sweep_expires_only_stale_pending(db: Session) -> None:
    ev = make_event(db)
    now = datetime.now(UTC)
    stale = Registration(
        event_id=ev.id,
        name="S",
        email="s@x.fi",
        quantity=1,
        status="pending",
        amount_cents=2000,
        expires_at=now - timedelta(seconds=1),
    )
    fresh = Registration(
        event_id=ev.id,
        name="F",
        email="f@x.fi",
        quantity=1,
        status="pending",
        amount_cents=2000,
        expires_at=now + timedelta(minutes=5),
    )
    done = Registration(
        event_id=ev.id,
        name="D",
        email="d@x.fi",
        quantity=1,
        status="confirmed",
        amount_cents=2000,
        expires_at=now - timedelta(hours=1),
        confirmed_at=now,
    )
    db.add_all([stale, fresh, done])
    db.commit()
    assert expire_stale_holds(db, now) == 1
    for r in (stale, fresh, done):
        db.refresh(r)
    assert (stale.status, fresh.status, done.status) == ("expired", "pending", "confirmed")
    assert expire_stale_holds(db, now) == 0
