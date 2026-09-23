import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.domain.registration_state import transition
from app.models import Registration
from app.repositories import registrations as repo
from app.services.stripe_gateway import StripeError, StripeGateway

log = logging.getLogger(__name__)


def _find_by_session(db: Session, obj: dict[str, Any]) -> Registration | None:
    reg = repo.by_session_id(db, obj.get("id", "")) if obj.get("id") else None
    if reg is not None:
        return reg
    raw = (obj.get("metadata") or {}).get("registration_id") or obj.get("client_reference_id")
    try:
        return repo.get(db, uuid.UUID(str(raw))) if raw else None
    except ValueError:
        return None


def handle_event(db: Session, event: dict[str, Any]) -> Registration | None:
    """Apply a Stripe event. Returns the registration if it was just confirmed (email due)."""
    kind = event.get("type")
    obj: dict[str, Any] = event.get("data", {}).get("object", {}) or {}
    if kind == "checkout.session.completed":
        reg = _find_by_session(db, obj)
        if reg is None:
            log.warning("checkout.session.completed for unknown session %s", obj.get("id"))
            return None
        nxt = transition(reg.status, "paid")
        if nxt is None:
            return None
        reg.status = nxt
        reg.confirmed_at = datetime.now(UTC)
        reg.stripe_payment_intent_id = obj.get("payment_intent") or reg.stripe_payment_intent_id
        if not reg.stripe_session_id and obj.get("id"):
            reg.stripe_session_id = obj["id"]
        db.commit()
        db.refresh(reg)
        return reg
    if kind == "checkout.session.expired":
        reg = _find_by_session(db, obj)
        nxt = transition(reg.status, "expired") if reg else None
        if reg is not None and nxt is not None:
            reg.status = nxt
            db.commit()
        return None
    if kind == "charge.refunded":
        pi = obj.get("payment_intent")
        reg = repo.by_payment_intent(db, pi) if pi else None
        nxt = transition(reg.status, "refunded") if reg else None
        if reg is not None and nxt is not None:
            reg.status = nxt
            db.commit()
        return None
    return None


def cancel_pending(db: Session, gateway: StripeGateway, reg: Registration) -> bool:
    nxt = transition(reg.status, "cancelled")
    if nxt is None:
        return False
    if reg.stripe_session_id:
        try:
            gateway.expire_session(reg.stripe_session_id)
        except StripeError as e:
            log.warning("Could not expire Stripe session %s: %s", reg.stripe_session_id, e)
    reg.status = nxt
    db.commit()
    return True
