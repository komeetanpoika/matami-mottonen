import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.domain.registration_state import EXPIRED, transition
from app.models import Registration
from app.repositories import registrations as repo
from app.services.stripe_gateway import StripeError, StripeGateway

log = logging.getLogger(__name__)

# A Checkout Session is only money in the bank once Stripe says so; a session
# can complete while the payment is still processing (or was never needed).
PAID_PAYMENT_STATUSES = ("paid", "no_payment_required")


def _find_by_session(
    db: Session, obj: dict[str, Any], *, for_update: bool = False
) -> Registration | None:
    session_id = obj.get("id", "")
    reg = repo.by_session_id(db, session_id, for_update=for_update) if session_id else None
    if reg is not None:
        return reg
    raw = (obj.get("metadata") or {}).get("registration_id") or obj.get("client_reference_id")
    try:
        return repo.get(db, uuid.UUID(str(raw)), for_update=for_update) if raw else None
    except ValueError:
        return None


def _fully_refunded(obj: dict[str, Any]) -> bool:
    if obj.get("refunded") is True:
        return True
    amount_refunded = obj.get("amount_refunded")
    amount = obj.get("amount")
    return amount_refunded is not None and amount is not None and amount_refunded == amount


def _confirm_paid(db: Session, obj: dict[str, Any], kind: str) -> Registration | None:
    """Apply the `paid` transition for a session we know is paid for."""
    reg = _find_by_session(db, obj, for_update=True)
    if reg is None:
        log.warning("%s for unknown session %s", kind, obj.get("id"))
        return None
    previous = reg.status
    nxt = transition(previous, "paid")
    if nxt is None:
        log.error("%s for registration %s already in state %s", kind, reg.id, previous)
        return None
    if previous == EXPIRED:
        log.warning(
            "%s for EXPIRED registration %s (session %s, %d cents): confirming anyway;"
            " event may now be overbooked",
            kind,
            reg.id,
            obj.get("id"),
            reg.amount_cents,
        )
    reg.status = nxt
    reg.confirmed_at = datetime.now(UTC)
    reg.stripe_payment_intent_id = obj.get("payment_intent") or reg.stripe_payment_intent_id
    if not reg.stripe_session_id and obj.get("id"):
        reg.stripe_session_id = obj["id"]
    db.commit()
    db.refresh(reg)
    return reg


def _expire(db: Session, obj: dict[str, Any], kind: str) -> None:
    reg = _find_by_session(db, obj, for_update=True)
    if reg is None:
        log.warning("%s for unknown session %s", kind, obj.get("id"))
        return
    nxt = transition(reg.status, "expired")
    if nxt is not None:
        reg.status = nxt
        db.commit()


def handle_event(db: Session, event: dict[str, Any]) -> Registration | None:
    """Apply a Stripe event. Returns the registration if it was just confirmed (email due)."""
    kind = event.get("type")
    obj: dict[str, Any] = event.get("data", {}).get("object", {}) or {}
    if kind == "checkout.session.completed":
        payment_status = obj.get("payment_status")
        if payment_status not in PAID_PAYMENT_STATUSES:
            # Delayed methods complete the session before the money lands. The
            # seat stays pending; async_payment_succeeded/failed (or the hold
            # sweep) settles it.
            log.info(
                "checkout.session.completed for session %s with payment_status %r:"
                " leaving the seat pending",
                obj.get("id"),
                payment_status,
            )
            return None
        return _confirm_paid(db, obj, kind)
    if kind == "checkout.session.async_payment_succeeded":
        return _confirm_paid(db, obj, kind)
    if kind in ("checkout.session.expired", "checkout.session.async_payment_failed"):
        _expire(db, obj, kind)
        return None
    if kind == "charge.refunded":
        pi = obj.get("payment_intent")
        reg = repo.by_payment_intent(db, pi, for_update=True) if pi else None
        if reg is None:
            log.warning("charge.refunded for unknown/absent payment_intent %s", pi)
            return None
        if not _fully_refunded(obj):
            log.info(
                "Partial refund for registration %s (payment_intent %s); leaving status %s",
                reg.id,
                pi,
                reg.status,
            )
            return None
        nxt = transition(reg.status, "refunded")
        if nxt is not None:
            reg.status = nxt
            db.commit()
        return None
    log.warning("Unhandled Stripe event type %s", kind)
    return None


def cancel_pending(db: Session, gateway: StripeGateway, reg: Registration) -> bool:
    locked = repo.get(db, reg.id, for_update=True)
    if locked is None:
        return False
    nxt = transition(locked.status, "cancelled")
    if nxt is None:
        return False
    if locked.stripe_session_id:
        try:
            gateway.expire_session(locked.stripe_session_id)
        except StripeError as e:
            log.warning("Could not expire Stripe session %s: %s", locked.stripe_session_id, e)
            return False
    locked.status = nxt
    db.commit()
    return True
