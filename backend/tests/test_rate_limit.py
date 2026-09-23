import time

from app.api.rate_limit import SlidingWindowLimiter


def test_hit_records_the_key_until_the_limit_is_reached() -> None:
    limiter = SlidingWindowLimiter(limit=3, window_seconds=60)
    key = "someone@example.com"

    assert limiter.hit(key) is True
    assert limiter.hit(key) is True
    assert limiter.hit(key) is True
    assert key in limiter._hits

    assert limiter.hit(key) is False
    assert key in limiter._hits


def test_clear_removes_the_key() -> None:
    limiter = SlidingWindowLimiter(limit=3, window_seconds=60)
    key = "someone@example.com"

    limiter.hit(key)
    assert key in limiter._hits

    limiter.clear(key)
    assert key not in limiter._hits


def test_a_fully_expired_window_is_evicted_on_the_next_hit() -> None:
    limiter = SlidingWindowLimiter(limit=2, window_seconds=1)
    key = "someone@example.com"

    limiter.hit(key)
    limiter.hit(key)
    assert len(limiter._hits[key]) == 2

    time.sleep(1.1)

    # The whole window aged out: the stale entries are gone and the key
    # starts fresh instead of being left behind as a permanent, unused dict
    # entry (which is exactly how an unbounded key space grows).
    assert limiter.hit(key) is True
    assert len(limiter._hits[key]) == 1
