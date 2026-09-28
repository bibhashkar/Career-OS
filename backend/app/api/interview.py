"""
Bi-directional WebSocket endpoint for stateful mock interview coaching.

This endpoint powers the interactive conversational interview simulator. It
maintains a continuous streaming session between the React chat window and the
LangGraph ``interview_app``.

Resumable Session Checkpointing:
The WebSocket connection URL incorporates a unique ``{thread_id}`` path parameter.
All turns, questions, and evaluations are checkpointed under this key:
  1. On connection: the endpoint queries ``aget_state(config)`` to inspect
     whether prior conversation exists for this ``thread_id``.
  2. If new session: the coach generates an opening technical challenge.
  3. If existing session: prior turns are preserved; new answers append to
     the active thread.
  4. On disconnect: the checkpoint remains persisted in PostgreSQL (or
     in-memory MemorySaver), allowing candidates to refresh or return later.

WebSocket Framing Protocol:
  - Client -> Server: ``{"type": "message", "content": "My answer..."}``
  - Heartbeat: ``{"type": "ping"}`` -> ``{"type": "pong"}``
  - Server -> Client: ``{"type": "message", "sender": "coach", "turn": 2}``
  - Errors: ``{"type": "error", "message": "..."}``
"""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.runnables import RunnableConfig

from app.agents.graph import interview_app
from app.agents.state import AgentState

router = APIRouter(tags=["Interview"])


@router.websocket("/api/interview/{thread_id}")
async def interview_websocket_endpoint(
    websocket: WebSocket,
    thread_id: str,
) -> None:
    """
    Stream interview dialogue bi-directionally keyed on thread_id checkpoint.

    Accepts incoming WebSocket connections, resolves thread state from the
    LangGraph checkpointer, handles ping/pong liveness heartbeats, and
    advances the coaching dialogue with each candidate answer.

    Args:
        websocket: The active FastAPI WebSocket connection.
        thread_id: Unique conversational session identifier.
    """
    await websocket.accept()
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    try:
        # Check current state or send initial question if new session
        current_state = await interview_app.aget_state(config)
        if not current_state or not current_state.values.get("interview_history"):
            init_state: AgentState = {
                "company_dossier": {
                    "company_name": "Target Company",
                    "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
                },
                "job_details": {"title": "Software Engineer"},
                "messages": [],
            }
            res = await interview_app.ainvoke(init_state, config=config)
            latest_msg = res.get("messages", [])[-1]["content"]
            await websocket.send_json(
                {
                    "type": "message",
                    "sender": "coach",
                    "content": latest_msg,
                    "turn": len(res.get("interview_history", [])),
                    "status": "active",
                }
            )

        # Message processing loop
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
            except Exception:
                data = {"content": raw_text}

            msg_type = data.get("type", "message")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            user_content = data.get("content", "").strip()
            if not user_content:
                continue

            # Advance LangGraph interview agent with candidate answer
            turn_state: AgentState = {
                "messages": [{"role": "user", "content": user_content}]
            }
            next_state = await interview_app.ainvoke(turn_state, config=config)
            coach_reply = next_state.get("messages", [])[-1]["content"]

            await websocket.send_json(
                {
                    "type": "message",
                    "sender": "coach",
                    "content": coach_reply,
                    "turn": len(next_state.get("interview_history", [])),
                    "status": "active",
                }
            )

    except WebSocketDisconnect:
        # Checkpoint is automatically persisted in checkpointer by thread_id
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
