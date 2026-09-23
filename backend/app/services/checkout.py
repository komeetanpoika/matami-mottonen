import logging
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.domain.capacity import seats_left
from app.models import Event, Registration
from app.repositories.events import holds_for, lock_published_by_slug
from app.services.mail_templates import confirmation
from app.services.mailer import Mailer
from app.services.stripe_gateway import StripeError, StripeGateway

log = logging.getLogger(__name__)


class CheckoutError(Exception):
    def __init__(self, code: str, seats_left: int | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.seats_left = seats_left


@dataclass(frozen=True)
class CheckoutResult:
    registration_id: uuid.UUID
    checkout_url: str | None
    confirmed: bool


def title_for(ev: Event, lang: str) -> str:
    if lang == "fi":
        return ev.title_fi or ev.title_en or "Event"
    return ev.title_en or ev.title_fi or "Event"


def start_checkout(
    db: Session,
    gateway: StripeGateway,
    *,
    slug: str,
    name: str,
    email: str,
    quantity: int,
    lang: str,
    now: datetime | None = None,
) -> CheckoutResult:
    with db.begin():
        # The "not started yet" filter tolerates a pre-lock clock (start times
        # are hours away); only the seat math below needs a post-lock `now`.
        ev = lock_published_by_slug(db, slug, now or datetime.now(UTC))
        if ev is None:
            raise CheckoutError("not_found")
        # Resolve `now` only after the row lock is acquired: computing it earlier
        # would let lock-wait time erode the hold margin over Stripe's expires_at
        # floor, and a stale `now` could miss holds that expired while we waited.
        now = now or datetime.now(UTC)
        left = seats_left(ev.capacity, holds_for(db, ev.id), now)
        if quantity > left:
            raise CheckoutError("sold_out", seats_left=left)
        reg = Registration(
            id=uuid.uuid4(),
            event_id=ev.id,
            name=name,
            email=email,
            quantity=quantity,
            amount_cents=ev.price_cents * quantity,
            lang=lang,
            expires_at=now + timedelta(minutes=settings.hold_minutes),
        )
        if ev.price_cents == 0:
            reg.status = "confirmed"
            reg.confirmed_at = now
            db.add(reg)
            return CheckoutResult(reg.id, None, confirmed=True)
        db.add(reg)
        db.flush()
        try:
            session = gateway.create_checkout_session(
                registration_id=str(reg.id),
                product_name=title_for(ev, lang),
                unit_amount=ev.price_cents,
                currency=ev.currency.lower(),
                quantity=quantity,
                customer_email=email,
                expires_at=reg.expires_at,
                success_url=f"{settings.public_base_url}/events/thanks?reg={reg.id}",
                cancel_url=f"{settings.public_base_url}/events/{ev.slug}?cancelled={reg.id}",
            )
        except StripeError as e:
            log.error("Stripe checkout failed for registration %s: %s", reg.id, e)
            raise CheckoutError("payment_unavailable") from e
        reg.stripe_session_id = session.id
        return CheckoutResult(reg.id, session.url, confirmed=False)


def confirmation_payload(reg: Registration, lang: str) -> tuple[str, str, str]:
    ev = reg.event
    subject, body = confirmation(
        lang,
        event_title=title_for(ev, lang),
        starts_at=ev.starts_at,
        location=ev.location,
        quantity=reg.quantity,
        amount_cents=reg.amount_cents,
        contact_email=settings.contact_email,
    )
    return reg.email, subject, body


def send_with_retry(mailer: Mailer, to: str, subject: str, body: str, attempts: int = 3) -> bool:
    for i in range(attempts):
        try:
            mailer.send(to, subject, body)
            return True
        except Exception as e:  # noqa: BLE001 — any transport error is retryable
            log.warning("Email to %s failed (attempt %d/%d): %s", to, i + 1, attempts, e)
            if i < attempts - 1:
                time.sleep(2**i)
    log.error("Giving up sending email to %s: %s", to, subject)
    return False
