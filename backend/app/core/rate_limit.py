"""
Sliding-window token bucket rate limiting middleware for FastAPI.

Protects resource-intensive multi-agent endpoints (like ``/api/cv/generate``)
and public endpoints against denial-of-service (DoS) and brute-force abuse.
Emits standard HTTP 429 Too Many Requests with RFC 6585 headers:
  - ``Retry-After``
  - ``X-RateLimit-Limit``
  - ``X-RateLimit-Remaining``
  - ``X-RateLimit-Reset``
"""

import threading
import time
from collections import defaultdict

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings


class InMemoryRateLimiter:
    """Thread-safe sliding-window rate limiter keyed by client identifier."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_rate_limited(
        self, key: str, limit: int, window_sec: int = 60
    ) -> tuple[bool, int, int]:
        """
        Check if the key exceeded limit within window_sec.

        Returns:
            (is_limited, remaining_requests, retry_after_sec)
        """
        now = time.time()
        cutoff = now - window_sec

        with self._lock:
            # Purge timestamps outside sliding window
            timestamps = [t for t in self._requests[key] if t > cutoff]
            self._requests[key] = timestamps

            if len(timestamps) >= limit:
                oldest_timestamp = timestamps[0]
                retry_after = max(1, int(oldest_timestamp + window_sec - now))
                return True, 0, retry_after

            # Record current request timestamp
            timestamps.append(now)
            remaining = max(0, limit - len(timestamps))
            return False, remaining, 0

    def reset(self) -> None:
        """Reset all rate limit counters (useful in tests)."""
        with self._lock:
            self._requests.clear()


rate_limiter = InMemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    HTTP middleware enforcing client IP rate limits on Career-OS routes.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Exempt health and metrics probes from rate limiting
        path = request.url.path
        if path in ("/health", "/metrics") or request.method == "OPTIONS":
            return await call_next(request)

        # Identify client by client host or X-Forwarded-For
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[
            0
        ].strip() or (request.client.host if request.client else "unknown")

        # Determine route-specific rate limit
        if path.startswith("/api/cv/generate"):
            limit = settings.CV_TAILOR_RATE_LIMIT_PER_MINUTE
            bucket_key = f"{client_ip}:cv_generate"
        else:
            limit = settings.RATE_LIMIT_PER_MINUTE
            bucket_key = f"{client_ip}:general"

        is_limited, remaining, retry_after = rate_limiter.is_rate_limited(
            key=bucket_key,
            limit=limit,
            window_sec=60,
        )

        if is_limited:
            problem = {
                "type": "https://errors.career-os.local/too-many-requests",
                "title": "Too Many Requests",
                "status": 429,
                "detail": f"Rate limit exceeded. Maximum {limit} requests per minute.",
                "instance": path,
            }
            error_response = JSONResponse(
                status_code=429,
                content=problem,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after),
                    "Content-Type": "application/problem+json",
                },
            )
            return error_response

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
