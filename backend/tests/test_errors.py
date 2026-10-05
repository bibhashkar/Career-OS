"""Unit tests for RFC 7807 problem details error handling."""

from fastapi.testclient import TestClient

from app.core.errors import create_problem_response
from app.main import app


def test_404_not_found_returns_problem_details() -> None:
    """Verify 404 responses conform to RFC 7807 application/problem+json."""
    client = TestClient(app)
    response = client.get("/api/non-existent-route-999")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert data["status"] == 404
    assert data["title"] == "Not Found"
    assert "detail" in data
    assert data["instance"] == "/api/non-existent-route-999"
    assert "correlation_id" in data


def test_422_validation_error_returns_problem_details() -> None:
    """Verify schema validation failures format as RFC 7807 with invalid_params."""
    client = TestClient(app)
    # POST invalid empty body to /api/cv/ingest
    response = client.post("/api/cv/ingest", json={})
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"

    data = response.json()
    assert data["status"] == 422
    assert data["title"] == "Unprocessable Entity"
    assert "invalid_params" in data
    assert len(data["invalid_params"]) > 0
    assert data["instance"] == "/api/cv/ingest"


def test_create_problem_response_helper() -> None:
    """Verify construct helper sets proper status code and media type."""
    resp = create_problem_response(
        status_code=403,
        title="Forbidden",
        detail="Insufficient permissions for resource.",
        instance="/api/secure",
    )
    assert resp.status_code == 403
    assert resp.media_type == "application/problem+json"
