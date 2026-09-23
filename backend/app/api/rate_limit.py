import threading
import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> bool:
        """Record a hit; return True if still within the limit."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and q[0] <= now - self.window:
                q.popleft()
            if not q:
                # A key with no hits left in the window is dead weight: drop
                # it so an unbounded stream of distinct keys (spoofed IPs,
                # made-up account emails) can't pin memory forever.
                del self._hits[key]
            if len(q) >= self.limit:
                return False
            q.append(now)
            self._hits[key] = q
            return True

    def clear(self, key: str) -> None:
        """Drop a key's recorded hits, e.g. after a successful login."""
        with self._lock:
            self._hits.pop(key, None)
