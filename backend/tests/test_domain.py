from datetime import UTC, datetime, timedelta

from app.domain.capacity import Hold, seats_left, seats_taken
from app.domain.registration_state import transition
from app.domain.slug import make_slug, slugify

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
LATER = NOW + timedelta(minutes=10)
EARLIER = NOW - timedelta(minutes=1)


def test_confirmed_always_counts_even_if_expires_at_passed() -> None:
    assert seats_taken([Hold(2, "confirmed", EARLIER)], NOW) == 2


def test_pending_counts_only_until_expiry() -> None:
    assert seats_taken([Hold(1, "pending", LATER)], NOW) == 1
    assert seats_taken([Hold(1, "pending", EARLIER)], NOW) == 0
    assert seats_taken([Hold(1, "pending", NOW)], NOW) == 0


def test_cancelled_and_expired_never_count() -> None:
    assert seats_taken([Hold(3, "cancelled", LATER), Hold(3, "expired", LATER)], NOW) == 0


def test_seats_left_never_negative() -> None:
    assert seats_left(2, [Hold(5, "confirmed", LATER)], NOW) == 0
    assert seats_left(10, [Hold(3, "confirmed", LATER), Hold(2, "pending", LATER)], NOW) == 5


def test_transitions() -> None:
    assert transition("pending", "paid") == "confirmed"
    assert transition("pending", "expired") == "expired"
    assert transition("pending", "cancelled") == "expired"
    assert transition("confirmed", "refunded") == "cancelled"
    assert transition("confirmed", "paid") is None
    # A payment that lands after the hold was swept still has to be honoured.
    assert transition("expired", "paid") == "confirmed"
    assert transition("cancelled", "refunded") is None
    assert transition("pending", "refunded") is None


def test_slugify_handles_finnish() -> None:
    assert slugify("Äänimalja-ilta: Syksy!") == "aanimalja-ilta-syksy"
    assert slugify("   ") == "event"


def test_make_slug_appends_suffix() -> None:
    assert make_slug("Sound Bowl", "ab3k") == "sound-bowl-ab3k"
    s = make_slug("Sound Bowl")
    assert s.startswith("sound-bowl-") and len(s) == len("sound-bowl-") + 4
