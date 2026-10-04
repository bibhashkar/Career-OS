"""Integration tests for bi-directional WebSocket mock interview endpoint."""

from fastapi.testclient import TestClient

from app.main import app


def test_interview_websocket_streaming_and_resumption() -> None:
    """Verify WebSocket bi-directional coaching exchange and session resumption."""
    client = TestClient(app)
    thread_id = "test_ws_thread_session_101"

    # Connect to WebSocket session
    with client.websocket_connect(f"/api/interview/{thread_id}") as ws:
        # Step 1: Receive initial opening question
        initial_msg = ws.receive_json()
        assert initial_msg["type"] == "message"
        assert initial_msg["sender"] == "coach"
        assert initial_msg["turn"] == 1
        assert "Welcome to your technical prep session" in initial_msg["content"]

        # Step 2: Send ping to test heartbeat
        ws.send_json({"type": "ping"})
        pong_msg = ws.receive_json()
        assert pong_msg["type"] == "pong"

        # Step 3: Send candidate technical answer
        candidate_answer = (
            "In my previous role, I designed a multi-agent workflow using LangGraph "
            "and PostgreSQL. We persisted execution checkpoints to PostgreSQL using "
            "PostgresSaver, which allowed us to pause and resume agent sessions."
        )
        ws.send_json({"type": "message", "content": candidate_answer})

        # Step 4: Receive coach evaluation and follow-up
        coach_response = ws.receive_json()
        assert coach_response["type"] == "message"
        assert coach_response["sender"] == "coach"
        assert coach_response["turn"] == 2
        assert "architectural awareness" in coach_response["content"]

    # Step 5: Resume session on same thread_id
    with client.websocket_connect(f"/api/interview/{thread_id}") as ws_resumed:
        # Next answer
        ws_resumed.send_json(
            {
                "type": "message",
                "content": (
                    "For failover, we used read replicas and connection pooling."
                ),
            }
        )
        resumed_reply = ws_resumed.receive_json()
        assert resumed_reply["type"] == "message"
        assert resumed_reply["turn"] >= 2


def test_interview_websocket_initializes_with_target_job() -> None:
    """Verify WebSocket initializes coaching grounded in target job and company."""
    client = TestClient(app)
    thread_id = "test_ws_thread_session_target_job"

    with client.websocket_connect(
        f"/api/interview/{thread_id}?company_name=NexusAI+Labs&title=Senior+Agentic+Engineer"
    ) as ws:
        initial_msg = ws.receive_json()
        assert initial_msg["type"] == "message"
        assert initial_msg["sender"] == "coach"
        assert initial_msg["turn"] == 1
        assert "Senior Agentic Engineer at NexusAI Labs" in initial_msg["content"]
        assert "Python" in initial_msg["content"]


def test_interview_websocket_resolves_job_by_id() -> None:
    """Verify WebSocket looks up job title and company when given job_id."""
    client = TestClient(app)
    thread_id = "test_ws_thread_session_job_id"

    with client.websocket_connect(
        f"/api/interview/{thread_id}?job_id=job-ai-001"
    ) as ws:
        initial_msg = ws.receive_json()
        assert initial_msg["type"] == "message"
        assert initial_msg["sender"] == "coach"
        assert "NexusAI Labs" in initial_msg["content"]
