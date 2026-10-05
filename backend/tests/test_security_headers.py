"""Unit tests for HTTP security headers and CORS policy enforcement."""

from fastapi.testclient import TestClient

from app.main import app


def test_security_headers_present_on_healthy_responses() -> None:
    """Verify OWASP security headers are attached to standard HTTP responses."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200

    headers = response.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert headers.get("permissions-policy") == (
        "geolocation=(), microphone=(), camera=()"
    )
    assert headers.get("x-xss-protection") == "0"
    assert "x-correlation-id" in headers


def test_security_headers_present_on_error_responses() -> None:
    """Verify security headers are preserved on 4xx/5xx error responses."""
    client = TestClient(app)
    response = client.get("/api/non-existent-route-888")
    assert response.status_code == 404

    headers = response.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_cors_preflight_allowed_origin() -> None:
    """Verify CORS preflight returns configured allowed origin, methods, and headers."""
    client = TestClient(app)
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,Authorization,X-Correlation-ID",
    }
    response = client.options("/health", headers=headers)
    assert response.status_code == 200

    res_headers = response.headers
    assert res_headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert res_headers.get("access-control-allow-credentials") == "true"

    allow_methods = res_headers.get("access-control-allow-methods", "")
    for method in ["GET", "POST", "PUT", "DELETE", "OPTIONS"]:
        assert method in allow_methods


def test_cors_disallows_untrusted_origin() -> None:
    """
    Verify untrusted origins outside CORS_ORIGINS do not receive allow headers.
    """
    client = TestClient(app)
    headers = {
        "Origin": "http://attacker.example.com",
        "Access-Control-Request-Method": "POST",
    }
    response = client.options("/health", headers=headers)
    assert (
        response.headers.get("access-control-allow-origin")
        != "http://attacker.example.com"
    )
