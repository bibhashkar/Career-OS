"""Bi-directional WebSocket endpoint for stateful mock interview coaching."""

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
    """Stream messages bi-directionally to coach_node keyed on thread_id checkpoint."""
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
