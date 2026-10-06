"""
Unit tests for Prometheus metrics registry and /metrics endpoint.
"""

from fastapi.testclient import TestClient

from app.core.metrics import metrics_registry
from app.main import app

client = TestClient(app)


def test_metrics_endpoint_exports_prometheus_format() -> None:
    """Verify that /metrics exports valid Prometheus text format."""
    # Issue a test request to populate request counts
    health_resp = client.get("/health")
    assert health_resp.status_code == 200

    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]

    body = resp.text
    assert "career_os_http_requests_total" in body
    assert "career_os_db_pool_size" in body
    assert "career_os_db_pool_checked_in" in body
    assert 'endpoint="/health"' in body


def test_metrics_registry_records_durations() -> None:
    """Verify metrics_registry records requests and computes summaries."""
    metrics_registry.record_request(
        method="POST",
        endpoint="/api/cv/generate",
        status_code=200,
        duration_sec=0.123,
    )

    output = metrics_registry.generate_prometheus_output()
    assert (
        'career_os_http_requests_total{method="POST",endpoint="/api/cv/generate",status="200"}'
        in output
    )
    assert (
        'career_os_http_request_duration_seconds{method="POST",endpoint="/api/cv/generate",metric="avg"}'
        in output
    )
