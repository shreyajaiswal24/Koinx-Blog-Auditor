"""In-memory audit state and WebSocket broadcast management."""

import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AuditState:
    """Tracks the currently running audit and manages WS client queues."""

    def __init__(self):
        self.is_running: bool = False
        self.progress: Dict[str, Any] = {}
        self._ws_queues: List[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        """Register a new WebSocket client. Returns its event queue."""
        q: asyncio.Queue = asyncio.Queue()
        self._ws_queues.append(q)
        # Send current state immediately if audit is running
        if self.is_running and self.progress:
            q.put_nowait(self.progress)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        """Remove a WebSocket client queue."""
        try:
            self._ws_queues.remove(q)
        except ValueError:
            pass

    def broadcast(self, event: Dict[str, Any]):
        """Push an event to all connected WebSocket clients.

        Safe to call from any thread — Queue.put_nowait is thread-safe in CPython.
        """
        self.progress = event
        for q in self._ws_queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def set_running(self, running: bool):
        self.is_running = running
        if not running:
            self.progress = {}


audit_state = AuditState()
