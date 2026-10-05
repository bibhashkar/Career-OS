"""Unit tests for resilient HTTP client execute_with_retry helper."""

import httpx
import pytest

from app.core.http import execute_with_retry


@pytest.mark.asyncio
async def test_execute_with_retry_succeeds_first_attempt() -> None:
    """Verify that successful requests return immediately without additional retries."""
    attempts = 0

    async def _mock_request() -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            status_code=200,
            json={"status": "ok"},
            request=httpx.Request("GET", "https://example.com"),
        )

    res = await execute_with_retry(_mock_request, max_retries=3, initial_delay=0.01)
    assert res is not None
    assert res.status_code == 200
    assert attempts == 1


@pytest.mark.asyncio
async def test_execute_with_retry_recovers_after_transient_failure() -> None:
    """Verify recovery when initial attempts return transient 503 or 429 errors."""
    attempts = 0

    async def _mock_flaky_request() -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            return httpx.Response(
                status_code=503,
                request=httpx.Request("GET", "https://example.com"),
            )
        return httpx.Response(
            status_code=200,
            json={"data": "success"},
            request=httpx.Request("GET", "https://example.com"),
        )

    res = await execute_with_retry(
        _mock_flaky_request, max_retries=3, initial_delay=0.01
    )
    assert res is not None
    assert res.status_code == 200
    assert attempts == 2


@pytest.mark.asyncio
async def test_execute_with_retry_handles_network_timeout() -> None:
    """Verify that network timeouts trigger retries up to max_retries limit."""
    attempts = 0

    async def _mock_timeout_request() -> httpx.Response:
        nonlocal attempts
        attempts += 1
        req = httpx.Request("GET", "https://example.com")
        raise httpx.ReadTimeout("Socket read timed out", request=req)

    res = await execute_with_retry(
        _mock_timeout_request, max_retries=3, initial_delay=0.01
    )
    assert res is None
    assert attempts == 3


@pytest.mark.asyncio
async def test_execute_with_retry_does_not_retry_client_errors() -> None:
    """Verify 4xx client errors (e.g. 400, 404) return immediately without retry."""
    attempts = 0

    async def _mock_client_error() -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            status_code=404,
            request=httpx.Request("GET", "https://example.com"),
        )

    res = await execute_with_retry(
        _mock_client_error, max_retries=3, initial_delay=0.01
    )
    assert res is not None
    assert res.status_code == 404
    assert attempts == 1
