from __future__ import annotations

import hashlib
import threading
from collections import defaultdict, deque
from time import time

from fastapi import HTTPException, Request, status

from app.core.config import settings

HEAVY_TOOL_COSTS = {
    "/api/tools/upscale/jobs": 3,
    "/api/tools/background-remove/jobs": 2,
    "/api/tools/pdf/merge/jobs": 2,
    "/api/tools/pdf/split/jobs": 2,
    "/api/tools/pdf/images-to-pdf/jobs": 2,
}


class WeightedSlidingWindowRateLimiter:
    def __init__(self, limit_per_minute: int) -> None:
        self.limit_per_minute = limit_per_minute
        self._events: dict[str, deque[tuple[float, int]]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, *, cost: int = 1) -> None:
        now = time()
        cutoff = now - 60
        with self._lock:
            events = self._events[key]
            while events and events[0][0] < cutoff:
                events.popleft()
            used = sum(weight for _, weight in events)
            if used + cost > self.limit_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="You have hit the upload rate limit for the last minute. Please wait a little and try again.",
                    headers={"Retry-After": "60"},
                )
            events.append((now, cost))


rate_limiter = WeightedSlidingWindowRateLimiter(settings.upload_rate_limit_per_minute)


def _rate_limit_key(request: Request) -> str:
    session_token = request.cookies.get(settings.session_cookie_name)
    if session_token:
        return f"session:{hashlib.sha256(session_token.encode()).hexdigest()}"
    visitor_token = request.cookies.get(settings.visitor_cookie_name)
    client_ip = request.client.host if request.client else "local"
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()
    if visitor_token:
        visitor_hash = hashlib.sha256(visitor_token.encode()).hexdigest()
        return f"visitor:{visitor_hash}:ip:{ip_hash}"
    return f"ip:{ip_hash}"


def enforce_upload_rate_limit(request: Request) -> None:
    cost = HEAVY_TOOL_COSTS.get(request.url.path, 1)
    rate_limiter.check(_rate_limit_key(request), cost=cost)
