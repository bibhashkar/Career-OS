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
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.runnables import RunnableConfig

from app.agents.graph import interview_app
from app.agents.state import AgentState
from app.agents.tools.company_intel import fetch_company_intel
from app.agents.tools.job_search import search_jobs
from app.core.config import settings
from app.core.logging import get_correlation_id

logger = logging.getLogger("career_os.interview")

router = APIRouter(tags=["Interview"])


@router.websocket("/api/interview/{thread_id}")
async def interview_websocket_endpoint(
    websocket: WebSocket,
    thread_id: str,
    job_id: str | None = None,
    company_name: str | None = None,
    title: str | None = None,
) -> None:
    """
    Stream interview dialogue bi-directionally keyed on thread_id checkpoint.

    Accepts incoming WebSocket connections, resolves thread state from the
    LangGraph checkpointer, handles ping/pong liveness heartbeats, and
    advances the coaching dialogue with each candidate answer.

    Args:
        websocket: The active FastAPI WebSocket connection.
        thread_id: Unique conversational session identifier.
        job_id: Optional target job listing ID to ground company tech stack prep.
        company_name: Optional target employer name.
        title: Optional target position title.
    """
    await websocket.accept()
    config: RunnableConfig = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": settings.GRAPH_RECURSION_LIMIT,
    }

    try:
        # Check current state or send initial question if new session
        current_state = await interview_app.aget_state(config)
        if not current_state or not current_state.values.get("interview_history"):
            resolved_company = company_name or "Target Company"
            resolved_title = title or "Software Engineer"

            # If job_id is provided, look up listing if title/company are unspecific
            if job_id and (
                resolved_company == "Target Company"
                or resolved_title == "Software Engineer"
            ):
                jobs = await search_jobs(query="")
                matched_job = next((j for j in jobs if j.get("id") == job_id), None)
                if matched_job:
                    resolved_company = matched_job.get("company_name", resolved_company)
                    resolved_title = matched_job.get("title", resolved_title)

            # Fetch researched company dossier to ground technical questions
            dossier = await fetch_company_intel(resolved_company)

            init_state: AgentState = {
                "current_job_id": job_id,
                "company_dossier": dossier,
                "job_details": {
                    "id": job_id,
                    "title": resolved_title,
                    "company_name": resolved_company,
                },
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
            except json.JSONDecodeError:
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
        cid = get_correlation_id() or uuid.uuid4().hex
        logger.exception(
            f"Unhandled error in interview WebSocket "
            f"[thread_id={thread_id}, correlation_id={cid}]: {exc}"
        )
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "title": "Interview Processing Error",
                    "message": "An error occurred during coaching evaluation.",
                    "correlation_id": cid,
                }
            )
        except Exception as ws_send_exc:
            logger.debug(
                f"Failed to send error frame over closed/broken WebSocket: "
                f"{ws_send_exc}"
            )
