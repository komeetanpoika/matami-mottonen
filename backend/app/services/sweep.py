import logging
from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Registration

log = logging.getLogger(__name__)


def expire_stale_holds(db: Session, now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    result = db.execute(
        update(Registration)
        .where(Registration.status == "pending", Registration.expires_at <= now)
        .values(status="expired")
    )
    db.commit()
    n = result.rowcount or 0
    if n:
        log.info("Expired %d stale holds", n)
    return n
