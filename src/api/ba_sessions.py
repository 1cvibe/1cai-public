from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from src.security.auth import get_auth_service
from src.services.ba_session_manager import ba_session_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ba-sessions", tags=["BA Sessions"])


@router.websocket("/ws/{session_id}")
async def ba_session_ws(
    websocket: WebSocket,
    session_id: str,
    user_id: Optional[str] = Query(default=None),
    role: Optional[str] = Query(default="analyst"),
    topic: Optional[str] = Query(default=None),
    token: Optional[str] = Query(default=None),
):
    """
    WebSocket endpoint for collaborative BA sessions.

    Query params:
    - user_id: уникальный идентификатор пользователя (если нет — берём из токена)
    - role: роль участника (analyst, lead, reviewer, observer)
    - topic: произвольный контекст сессии
    """
    if token:
        try:
            principal = get_auth_service().decode_token(token)
            user_id = user_id or principal.user_id
            if principal.roles:
                role = principal.roles[0]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to decode token for BA session: %s", exc)
    if not user_id:
        user_id = "anonymous"
    try:
        await ba_session_manager.join_session(
            session_id,
            websocket,
            user_id=user_id,
            role=role or "analyst",
            topic=topic,
        )
        await ba_session_manager.broadcast(
            session_id,
            {"type": "system", "event": "user_joined", "user_id": user_id, "role": role},
            sender="system",
        )

        while True:
            data = await websocket.receive_json()
            message_type = data.get("type") or "message"
            if message_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            elif message_type == "leave":
                await websocket.close()
                break
            else:
                await ba_session_manager.broadcast(
                    session_id,
                    data,
                    sender=user_id,
                )
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # pragma: no cover - network errors
        logger.error("BA session websocket error: %s", exc)
    finally:
        await ba_session_manager.leave_session(session_id, user_id)
        await ba_session_manager.broadcast(
            session_id,
            {"type": "system", "event": "user_left", "user_id": user_id},
            sender="system",
        )


@router.get("")
async def list_sessions():
    """List active BA sessions."""
    return {"sessions": ba_session_manager.list_sessions()}


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Get state for a BA session."""
    state = ba_session_manager.get_session_state(session_id)
    if not state:
        return JSONResponse(status_code=404, content={"detail": "Session not found"})
    return state

