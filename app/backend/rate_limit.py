"""Basic rate limiter for VeriCoach backend."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import ClassVar

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """Sliding-window rate limiter per client identifier."""

    _instances: ClassVar[dict[str, InMemoryRateLimiter]] = {}

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.rate = requests_per_minute
        self.window_seconds = 60.0
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds

        # Clean timestamps older than window
        timestamps = [t for t in self._requests[client_id] if t > cutoff]
        self._requests[client_id] = timestamps

        if len(timestamps) >= self.rate:
            return False

        self._requests[client_id].append(now)
        return True

    def reset(self) -> None:
        """Reset rate limit buckets (useful for tests)."""
        self._requests.clear()


_default_limiter = InMemoryRateLimiter(requests_per_minute=60)


def check_rate_limit(request: Request) -> None:
    """Dependency enforcing rate limits per client IP or API Key."""
    # Use X-Forwarded-For if available, otherwise client host
    client_ip = request.client.host if request.client else "127.0.0.1"
    api_key = request.headers.get("X-API-Key", "")
    identifier = f"{client_ip}:{api_key}" if api_key else client_ip

    if not _default_limiter.is_allowed(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before making further requests.",
        )
