"""Unit tests for REST request payload limits and WebSocket frame size caps."""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def test_cv_ingest_rejects_oversized_payload() -> None:
    """
    Verify POST /api/cv/ingest rejects resume text exceeding MAX_CV_RAW_TEXT_LENGTH.
    """
    client = TestClient(app)
    oversized_text = "A" * (settings.MAX_CV_RAW_TEXT_LENGTH + 10)
    response = client.post(
        "/api/cv/ingest",
        json={"raw_text": oversized_text},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["title"] == "Unprocessable Entity"


def test_feedback_rejects_oversized_payload() -> None:
    """
    Verify POST /api/feedback rejects feedback text exceeding MAX_FEEDBACK_TEXT_LENGTH.
    """
    client = TestClient(app)
    oversized_feedback = "F" * (settings.MAX_FEEDBACK_TEXT_LENGTH + 5)
    response = client.post(
        "/api/feedback",
        json={"thread_id": "thread-limit-test", "user_feedback": oversized_feedback},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["title"] == "Unprocessable Entity"


def test_cv_generate_rejects_excessive_skill_list() -> None:
    """Verify POST /api/cv/generate rejects required_skills list with >50 items."""
    client = TestClient(app)
    excessive_skills = [f"Skill_{i}" for i in range(55)]
    response = client.post(
        "/api/cv/generate",
        json={
            "job_id": "job-limit-test",
            "required_skills": excessive_skills,
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert data["title"] == "Unprocessable Entity"


def test_websocket_rejects_oversized_frame() -> None:
    """
    Verify WebSocket endpoint returns Payload Too Large error frame on oversized input.
    """
    client = TestClient(app)
    thread_id = "test_ws_size_cap"
    with client.websocket_connect(f"/api/interview/{thread_id}") as ws:
        # First receive opening coach question
        opening = ws.receive_json()
        assert opening["type"] == "message"
        assert opening["sender"] == "coach"

        # Send oversized frame > MAX_WS_FRAME_BYTES (16KB)
        oversized_payload = "X" * (settings.MAX_WS_FRAME_BYTES + 500)
        ws.send_text(oversized_payload)

        # Receive error frame
        reply = ws.receive_json()
        assert reply["type"] == "error"
        assert reply["title"] == "Payload Too Large"
        assert "exceeds maximum allowed size" in reply["message"]
