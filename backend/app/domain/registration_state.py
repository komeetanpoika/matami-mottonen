PENDING = "pending"
CONFIRMED = "confirmed"
CANCELLED = "cancelled"
EXPIRED = "expired"

_TRANSITIONS: dict[tuple[str, str], str] = {
    (PENDING, "paid"): CONFIRMED,
    (PENDING, "expired"): EXPIRED,
    (PENDING, "cancelled"): EXPIRED,
    (CONFIRMED, "refunded"): CANCELLED,
    # The sweep (or Stripe's own session expiry) can release a hold while the
    # customer is still on the payment page. If the payment then succeeds we
    # must honour it: money has changed hands, so confirm and let a human sort
    # out any overbooking, rather than leave a paid seat in a dead state.
    (EXPIRED, "paid"): CONFIRMED,
}


def transition(current: str, trigger: str) -> str | None:
    """Next status for `trigger`, or None when the trigger does not apply (idempotent no-op)."""
    return _TRANSITIONS.get((current, trigger))
