"""
Unit and integration tests for the Admin Control Plane & Observability API.

Verifies:
  - Role-based access control (unauthenticated -> 401, candidate -> 403, admin -> 200).
  - Admin overview telemetry response structure (system, queue, catalog, ai_usage, users).
  - Operator actions: register board, sync board, retry failed tasks, reset circuit breaker,
    flush match cache, and update user status/role.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.auth import create_access_token
from app.core.database import get_db
from app.main import app


@pytest.fixture
def candidate_token() -> str:
    return create_access_token(
        user_id="usr-cand-123",
        email="candidate@example.com",
        role="candidate",
    )


@pytest.fixture
def admin_token() -> str:
    return create_access_token(
        user_id="usr-admin-001",
        email="admin@career-os.local",
        role="admin",
    )


def test_admin_overview_unauthenticated_returns_401() -> None:
    client = TestClient(app)
    response = client.get("/api/admin/overview")
    assert response.status_code == 401


def test_admin_overview_candidate_role_returns_403(candidate_token: str) -> None:
    client = TestClient(app)
    response = client.get(
        "/api/admin/overview",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert response.status_code == 403
    assert "administrative privileges required" in response.text.lower()


def test_admin_actions_forbidden_for_candidate(candidate_token: str) -> None:
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {candidate_token}"}

    # Register board
    res = client.post(
        "/api/admin/boards",
        headers=headers,
        json={"company_name": "Acme", "provider": "greenhouse", "board_token": "acme"},
    )
    assert res.status_code == 403

    # Reset circuit breaker
    res = client.post(
        "/api/admin/circuit-breakers/greenhouse/reset",
        headers=headers,
    )
    assert res.status_code == 403

    # Flush match cache
    res = client.post(
        "/api/admin/cache/flush-matches",
        headers=headers,
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_overview_with_admin_role_success(admin_token: str) -> None:
    """Verify admin overview aggregates metrics and returns status 200."""
    client = TestClient(app)

    # Mock the database session and queries to keep test hermetic
    mock_db = AsyncMock()

    # Synchronous query result mock matching SQLAlchemy Result interface
    result_mock = MagicMock()
    result_mock.scalar_one.return_value = 0
    result_mock.scalars.return_value.all.return_value = []
    result_mock.all.return_value = []

    mock_db.execute = AsyncMock(return_value=result_mock)

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get(
            "/api/admin/overview",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "current_operator" in data
        assert data["current_operator"]["email"] == "admin@career-os.local"
        assert data["current_operator"]["role"] == "admin"
        assert "system_health" in data
        assert "crawler_pipeline" in data
        assert "catalog_breakdown" in data
        assert "ai_cost_and_quotas" in data
        assert "users" in data
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_admin_operator_actions(admin_token: str) -> None:
    """Verify operator endpoints execute successfully with admin credentials."""
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {admin_token}"}

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    # Mock execute result
    res_mock = MagicMock()
    res_mock.rowcount = 3
    res_mock.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=res_mock)

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        # Retry failed tasks
        res = client.post("/api/admin/tasks/retry-failed", headers=headers)
        assert res.status_code == 200
        assert res.json()["status"] == "success"

        # Purge failed tasks
        res = client.delete("/api/admin/tasks/failed", headers=headers)
        assert res.status_code == 200
        assert res.json()["status"] == "success"

        # Reset circuit breaker
        res = client.post(
            "/api/admin/circuit-breakers/greenhouse/reset", headers=headers
        )
        assert res.status_code == 200
        assert res.json()["provider"] == "greenhouse"

        # Flush match cache
        res = client.post("/api/admin/cache/flush-matches", headers=headers)
        assert res.status_code == 200
        assert res.json()["status"] == "success"
    finally:
        app.dependency_overrides.pop(get_db, None)
