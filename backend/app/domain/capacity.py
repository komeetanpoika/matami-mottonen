from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Hold:
    quantity: int
    status: str
    expires_at: datetime


def seats_taken(holds: Iterable[Hold], now: datetime) -> int:
    total = 0
    for h in holds:
        if h.status == "confirmed":
            total += h.quantity
        elif h.status == "pending" and h.expires_at > now:
            total += h.quantity
    return total


def seats_left(capacity: int, holds: Iterable[Hold], now: datetime) -> int:
    return max(0, capacity - seats_taken(holds, now))
