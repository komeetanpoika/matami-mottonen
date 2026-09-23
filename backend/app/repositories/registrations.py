import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Registration


def get(db: Session, reg_id: uuid.UUID) -> Registration | None:
    return db.get(Registration, reg_id)


def by_session_id(db: Session, session_id: str) -> Registration | None:
    return db.scalar(select(Registration).where(Registration.stripe_session_id == session_id))


def by_payment_intent(db: Session, payment_intent: str) -> Registration | None:
    return db.scalar(
        select(Registration).where(Registration.stripe_payment_intent_id == payment_intent)
    )
