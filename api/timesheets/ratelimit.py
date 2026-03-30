"""A small in-memory sliding window limiter for the auth endpoints.

Good enough for a single API process; put a shared store behind it before
running several replicas.
"""

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> float | None:
        """Record an attempt. Returns seconds to wait when over the limit, else None."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= now - self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return self.window - (now - hits[0])
            hits.append(now)
            return None

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


auth_limiter = RateLimiter(limit=10, window_seconds=300)


def limit_auth(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    retry_after = auth_limiter.hit(f"{client}:{request.url.path}")
    if retry_after is not None:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many attempts, try again in a few minutes",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )
