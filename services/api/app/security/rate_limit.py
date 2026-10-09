from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from app.config import settings


class RateLimiter:
    def __init__(self, per_minute: int | None = None) -> None:
        self.per_minute = per_minute or settings.rate_limit_per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        window = 60.0
        with self._lock:
            bucket = self._hits[key]
            while bucket and now - bucket[0] > window:
                bucket.popleft()
            if len(bucket) >= self.per_minute:
                return False
            bucket.append(now)
            return True


limiter = RateLimiter()
