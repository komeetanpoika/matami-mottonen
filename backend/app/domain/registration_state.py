PENDING = "pending"
CONFIRMED = "confirmed"
CANCELLED = "cancelled"
EXPIRED = "expired"

_TRANSITIONS: dict[tuple[str, str], str] = {
    (PENDING, "paid"): CONFIRMED,
    (PENDING, "expired"): EXPIRED,
    (PENDING, "cancelled"): EXPIRED,
    (CONFIRMED, "refunded"): CANCELLED,
}


def transition(current: str, trigger: str) -> str | None:
    """Next status for `trigger`, or None when the trigger does not apply (idempotent no-op)."""
    return _TRANSITIONS.get((current, trigger))
