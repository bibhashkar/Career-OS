"""
Prometheus metrics collector and instrumentation for Career-OS.

Exports standard Prometheus text format metrics at ``/metrics``:
  - ``career_os_http_requests_total`` (method, endpoint, status_code)
  - ``career_os_http_request_duration_seconds`` (method, endpoint)
  - ``career_os_db_pool_size``
  - ``career_os_db_pool_checked_in``
  - ``career_os_db_pool_checked_out``
  - ``career_os_db_pool_overflow``
"""

import threading
import time
from collections import defaultdict
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.database import engine


class MetricsRegistry:
    """Thread-safe Prometheus metrics collector and exposition formatter."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._request_counts: dict[tuple[str, str, int], int] = defaultdict(int)
        self._request_durations: dict[tuple[str, str], list[float]] = defaultdict(list)

    def record_request(
        self, method: str, endpoint: str, status_code: int, duration_sec: float
    ) -> None:
        """Record an incoming HTTP request completion."""
        with self._lock:
            self._request_counts[(method, endpoint, status_code)] += 1
            # Keep up to 100 recent durations per endpoint to bound memory
            durations = self._request_durations[(method, endpoint)]
            durations.append(duration_sec)
            if len(durations) > 100:
                self._request_durations[(method, endpoint)] = durations[-100:]

    def generate_prometheus_output(self) -> str:
        """Serialize registered metrics to standard Prometheus exposition format."""
        lines: list[str] = [
            "# HELP career_os_http_requests_total Total HTTP requests.",
            "# TYPE career_os_http_requests_total counter",
        ]

        with self._lock:
            for (
                method,
                endpoint,
                status_code,
            ), count in sorted(self._request_counts.items()):
                lines.append(
                    f'career_os_http_requests_total{{method="{method}",'
                    f'endpoint="{endpoint}",status="{status_code}"}} {count}'
                )

            lines.extend(
                [
                    "# HELP career_os_http_request_duration_seconds Request latencies.",
                    "# TYPE career_os_http_request_duration_seconds gauge",
                ]
            )

            for (method, endpoint), durations in sorted(
                self._request_durations.items()
            ):
                if durations:
                    avg_duration = sum(durations) / len(durations)
                    lines.append(
                        f'career_os_http_request_duration_seconds{{method="{method}",'
                        f'endpoint="{endpoint}",metric="avg"}} {avg_duration:.6f}'
                    )

        # Database pool metrics directly queried from SQLAlchemy engine pool
        pool: Any = engine.pool
        pool_size = pool.size() if hasattr(pool, "size") else 0
        checked_in = pool.checkedin() if hasattr(pool, "checkedin") else 0
        checked_out = pool.checkedout() if hasattr(pool, "checkedout") else 0
        overflow = pool.overflow() if hasattr(pool, "overflow") else 0

        lines.extend(
            [
                "# HELP career_os_db_pool_size SQLAlchemy pool size.",
                "# TYPE career_os_db_pool_size gauge",
                f"career_os_db_pool_size {pool_size}",
                "# HELP career_os_db_pool_checked_in Available pool connections.",
                "# TYPE career_os_db_pool_checked_in gauge",
                f"career_os_db_pool_checked_in {checked_in}",
                "# HELP career_os_db_pool_checked_out Active connections in use.",
                "# TYPE career_os_db_pool_checked_out gauge",
                f"career_os_db_pool_checked_out {checked_out}",
                "# HELP career_os_db_pool_overflow Active overflow connections.",
                "# TYPE career_os_db_pool_overflow gauge",
                f"career_os_db_pool_overflow {overflow}",
            ]
        )

        return "\n".join(lines) + "\n"


metrics_registry = MetricsRegistry()


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware recording HTTP request counts and durations into MetricsRegistry."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Avoid recording metrics on the metrics endpoint itself
        path = request.url.path
        if path == "/metrics":
            return await call_next(request)

        start_time = time.monotonic()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.monotonic() - start_time
            metrics_registry.record_request(
                method=request.method,
                endpoint=path,
                status_code=status_code,
                duration_sec=duration,
            )
