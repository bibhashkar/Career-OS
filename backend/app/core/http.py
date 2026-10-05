"""
Resilient asynchronous HTTP client helpers with timeouts and exponential backoff.

Third-party API services (job aggregators, neural search engines, company intelligence)
are subject to network jitter, rate limiting (HTTP 429), and transient failures
(HTTP 5xx). This module provides an async execution utility that wraps HTTP operations
with bounded retries, exponential backoff, and strict connection and read timeouts.
"""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

import httpx

logger = logging.getLogger("career_os.http")

DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=3.0)


async def execute_with_retry(
    func: Callable[[], Coroutine[Any, Any, httpx.Response]],
    *,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504),
    operation_name: str = "HTTP request",
) -> httpx.Response | None:
    """
    Execute an async HTTP call with bounded retries and exponential backoff.

    Args:
        func: Async zero-argument callable returning an httpx.Response.
        max_retries: Maximum number of attempts before aborting.
        initial_delay: Initial delay in seconds before the first retry.
        backoff_factor: Multiplier applied to the delay after each retry.
        retry_statuses: HTTP status codes triggering a retry.
        operation_name: Human-readable identifier for structured logging.

    Returns:
        The successful httpx.Response, or None if retries were exhausted.
    """
    delay = initial_delay
    last_response: httpx.Response | None = None

    for attempt in range(1, max_retries + 1):
        try:
            response = await func()
            last_response = response
            if response.status_code not in retry_statuses:
                return response

            logger.warning(
                f"{operation_name} returned status {response.status_code} "
                f"(attempt {attempt}/{max_retries}); retrying in {delay:.2f}s..."
            )
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.warning(
                f"{operation_name} encountered network/timeout error: {exc} "
                f"(attempt {attempt}/{max_retries}); retrying in {delay:.2f}s..."
            )

        if attempt < max_retries:
            await asyncio.sleep(delay)
            delay *= backoff_factor

    return last_response
