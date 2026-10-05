"""Unit tests for authentication, JWT signing, and WebSocket thread protection."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.auth import (
    create_access_token,
    decode_access_token,
)
from app.main import app


def test_create_and_decode_access_token() -> None:
    """Verify standard HS256 JWT encoding and decoding round-trip."""
    token = create_access_token(
        user_id="usr-test-123",
        email="candidate@example.com",
        role="candidate",
    )
    user = decode_access_token(token)
    assert user.user_id == "usr-test-123"
    assert user.email == "candidate@example.com"
    assert user.role == "candidate"


def test_decode_expired_token_raises_401() -> None:
    """Verify expired tokens are rejected with HTTP 401."""
    expired_token = create_access_token(
        user_id="usr-expired",
        expires_in_seconds=-60,
    )
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(expired_token)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_decode_tampered_token_raises_401() -> None:
    """Verify signature verification fails when token payload is altered."""
    token = create_access_token(user_id="usr-valid")
    parts = token.split(".")
    tampered_token = f"{parts[0]}.eyJzdWIiOiAiaGFja2VyIn0.{parts[2]}"
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(tampered_token)
    assert exc_info.value.status_code == 401
    assert "signature" in exc_info.value.detail.lower()


def test_rest_endpoint_with_valid_bearer_token() -> None:
    """Verify REST endpoints authenticate callers presenting valid Bearer JWT."""
    token = create_access_token(user_id="usr-rest-test")
    client = TestClient(app)
    response = client.post(
        "/api/jobs/search",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "AI Engineer"},
    )
    assert response.status_code == 200


def test_rest_endpoint_with_invalid_bearer_token() -> None:
    """Verify REST endpoints reject requests with malformed or tampered Bearer token."""
    client = TestClient(app)
    response = client.post(
        "/api/jobs/search",
        headers={"Authorization": "Bearer invalid.tampered.token"},
        json={"query": "AI Engineer"},
    )
    assert response.status_code == 401


def test_websocket_connects_with_valid_token() -> None:
    """Verify WebSocket endpoint authorizes connection using query param token."""
    token = create_access_token(user_id="usr-ws-owner-1")
    thread_id = "test_ws_auth_thread_1"
    client = TestClient(app)
    with client.websocket_connect(f"/api/interview/{thread_id}?token={token}") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "message"
        assert msg["sender"] == "coach"


def test_websocket_rejects_invalid_token() -> None:
    """Verify WebSocket rejects connection with invalid/tampered token."""
    thread_id = "test_ws_auth_invalid"
    client = TestClient(app)
    with client.websocket_connect(
        f"/api/interview/{thread_id}?token=invalid.token.data"
    ) as ws:
        err = ws.receive_json()
        assert err["type"] == "error"
        assert err["title"] == "Unauthorized"


def test_websocket_prevents_thread_hijacking() -> None:
    """Verify Candidate B cannot connect to a thread already owned by Candidate A."""
    token_a = create_access_token(user_id="candidate-alice")
    token_b = create_access_token(user_id="candidate-bob")
    thread_id = "shared_interview_session_777"
    client = TestClient(app)

    # 1. Candidate A connects and initializes thread
    with client.websocket_connect(
        f"/api/interview/{thread_id}?token={token_a}"
    ) as ws_a:
        msg = ws_a.receive_json()
        assert msg["type"] == "message"

    # 2. Candidate B attempts to connect to Candidate A's thread
    with client.websocket_connect(
        f"/api/interview/{thread_id}?token={token_b}"
    ) as ws_b:
        err = ws_b.receive_json()
        assert err["type"] == "error"
        assert err["title"] == "Unauthorized"
