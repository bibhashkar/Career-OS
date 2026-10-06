import pytest
from fastapi.testclient import TestClient

from app.core.rate_limit import rate_limiter
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_rate_limiter() -> None:
    rate_limiter.reset()
    yield
    rate_limiter.reset()


def test_rate_limiter_allows_requests_under_threshold() -> None:
    """Verify that requests below the rate limit succeed with RFC 6585 headers."""
    resp = client.get("/health")
    # Health endpoint is exempt from limiting
    assert resp.status_code == 200

    resp2 = client.post(
        "/api/jobs/search",
        json={"query": "Engineer", "location": "Remote", "visa_required": False},
    )
    assert resp2.status_code in (200, 422)
    assert "X-RateLimit-Limit" in resp2.headers
    assert "X-RateLimit-Remaining" in resp2.headers


def test_rate_limiter_blocks_and_returns_429_when_exceeded() -> None:
    """Verify that requests exceeding threshold return 429 Too Many Requests."""
    # Artificially trigger rate limit by simulating limit calls
    key = "testclient:cv_generate"
    for _ in range(20):
        is_limited, _, _ = rate_limiter.is_rate_limited(
            key=key, limit=20, window_sec=60
        )
        assert not is_limited

    # 21st call should trigger rate limiting
    is_limited, remaining, retry_after = rate_limiter.is_rate_limited(
        key=key, limit=20, window_sec=60
    )
    assert is_limited
    assert remaining == 0
    assert retry_after > 0


def test_rate_limit_middleware_returns_rfc7807_problem() -> None:
    """Verify 429 response structure matches RFC 7807 problem details."""
    # Saturate rate limiter for the test client IP on general bucket
    key = "testclient:general"
    for _ in range(120):
        rate_limiter.is_rate_limited(key=key, limit=120, window_sec=60)

    resp = client.post(
        "/api/jobs/search",
        json={"query": "Engineer", "location": "Remote", "visa_required": False},
    )
    assert resp.status_code == 429
    assert resp.headers.get("retry-after") is not None
    assert "application/problem+json" in resp.headers.get("content-type", "")

    data = resp.json()
    assert data["status"] == 429
    assert data["title"] == "Too Many Requests"
    assert "Maximum 120 requests" in data["detail"]
