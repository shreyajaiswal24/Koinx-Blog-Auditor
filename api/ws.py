"""WebSocket endpoint for real-time audit progress."""

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.state import audit_state

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/audit")
async def audit_ws(websocket: WebSocket):
    """Stream audit progress events to the browser."""
    await websocket.accept()
    queue = audit_state.subscribe()
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"WS closed: {e}")
    finally:
        audit_state.unsubscribe(queue)
