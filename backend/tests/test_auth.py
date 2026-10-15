from collections.abc import AsyncGenerator

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.database import get_db
from app.main import app


def test_hash_and_verify_password() -> None:
    """Verify bcrypt password hashing and verification."""
    raw_pw = "SuperSecurePassword123!"
    pw_hash = hash_password(raw_pw)
    assert pw_hash != raw_pw
    assert verify_password(raw_pw, pw_hash) is True
    assert verify_password("WrongPassword123!", pw_hash) is False


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


@pytest.mark.asyncio
async def test_auth_register_login_and_me_flow(
    db_session: AsyncSession,
) -> None:
    """Verify registration, login, and profile retrieval endpoints."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Register new user
            reg_payload = {
                "email": "cand1@example.com",
                "password": "StrongPassword123!",
                "full_name": "Candidate One",
                "visa_status": "H-1B",
                "citizenship_country_code": "US",
                "preferred_locations": ["San Francisco, CA"],
                "remote_preference": "Remote",
            }
            reg_resp = await client.post("/api/auth/register", json=reg_payload)
            assert reg_resp.status_code == 201
            reg_data = reg_resp.json()
            assert "access_token" in reg_data
            assert reg_data["user"]["email"] == "cand1@example.com"
            assert len(reg_data["user"]["personas"]) == 1
            assert reg_data["user"]["personas"][0]["is_common_persona"] is True
            assert reg_data["user"]["personas"][0]["name"] == "Universal Profile"

            token = reg_data["access_token"]

            # 2. Duplicate registration rejected
            dup_resp = await client.post("/api/auth/register", json=reg_payload)
            assert dup_resp.status_code == 400

            # 3. Login with credentials
            login_resp = await client.post(
                "/api/auth/login",
                json={
                    "email": "cand1@example.com",
                    "password": "StrongPassword123!",
                },
            )
            assert login_resp.status_code == 200
            login_data = login_resp.json()
            assert login_data["user"]["full_name"] == "Candidate One"

            # 4. Login with bad password
            bad_pw_resp = await client.post(
                "/api/auth/login",
                json={
                    "email": "cand1@example.com",
                    "password": "WrongPassword",
                },
            )
            assert bad_pw_resp.status_code == 401

            # 5. Access /api/auth/me
            me_resp = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert me_resp.status_code == 200
            me_data = me_resp.json()
            assert me_data["email"] == "cand1@example.com"
            assert len(me_data["personas"]) == 1
            assert me_data["personas"][0]["is_common_persona"] is True
    finally:
        app.dependency_overrides.pop(get_db, None)
