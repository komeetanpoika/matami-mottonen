import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Registration


def get(db: Session, reg_id: uuid.UUID, *, for_update: bool = False) -> Registration | None:
    if for_update:
        return db.get(Registration, reg_id, with_for_update=True)
    return db.get(Registration, reg_id)


def by_session_id(db: Session, session_id: str, *, for_update: bool = False) -> Registration | None:
    stmt = select(Registration).where(Registration.stripe_session_id == session_id)
    if for_update:
        stmt = stmt.with_for_update()
    return db.scalar(stmt)


def by_payment_intent(
    db: Session, payment_intent: str, *, for_update: bool = False
) -> Registration | None:
    stmt = select(Registration).where(Registration.stripe_payment_intent_id == payment_intent)
    if for_update:
        stmt = stmt.with_for_update()
    return db.scalar(stmt)
