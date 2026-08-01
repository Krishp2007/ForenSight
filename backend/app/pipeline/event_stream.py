"""
Event Stream — ForenSight AI
================================
Real-time SSE (Server-Sent Events) pipeline for streaming live processing
status updates back to the frontend during evidence ingestion.

The frontend polling approach (every 4 s) works fine for most cases, but
for large evidence files this module allows the API to push status updates
immediately via an SSE stream:

  GET /cases/{case_id}/evidence/{evidence_id}/stream

The stream emits JSON-encoded status events:
  data: {"evidence_id": "...", "status": "parsing", "progress": 42, "message": "..."}

Usage in the processing pipeline:
  from backend.app.pipeline.event_stream import EventStream
  EventStream.publish(evidence_id, status="parsing", progress=30, message="Parsed 300/1000 events")
"""

import asyncio
import json
import logging
from collections import defaultdict
from typing import Any, AsyncIterator, Dict

logger = logging.getLogger(__name__)

# In-memory pub/sub channels: evidence_id → list of asyncio.Queue
_channels: Dict[str, list] = defaultdict(list)


class EventStream:
    """
    Lightweight in-process SSE pub/sub.
    Works within a single FastAPI process; for multi-worker setups
    this should be backed by Redis pub/sub instead.
    """

    @classmethod
    def publish(
        cls,
        evidence_id: str,
        status: str,
        progress: int = 0,
        message: str = "",
        extra: Dict[str, Any] | None = None,
    ) -> None:
        """
        Publish a status update event for a given evidence ID.
        All active SSE listeners for that evidence will receive it immediately.
        """
        payload = {
            "evidence_id": evidence_id,
            "status": status,
            "progress": progress,
            "message": message,
            **(extra or {}),
        }
        data = json.dumps(payload)
        dead = []
        for q in _channels.get(evidence_id, []):
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                dead.append(q)
        # Clean up full/disconnected queues
        for q in dead:
            try:
                _channels[evidence_id].remove(q)
            except ValueError:
                pass

    @classmethod
    async def subscribe(cls, evidence_id: str) -> AsyncIterator[str]:
        """
        Async generator that yields SSE-formatted strings for a given
        evidence ID until a terminal status ('parsed' or 'failed') is received
        or the client disconnects.

        Yields strings in SSE format:
          data: {...json...}\n\n
        """
        q: asyncio.Queue = asyncio.Queue(maxsize=50)
        _channels[evidence_id].append(q)
        logger.debug(f"[EventStream] Client subscribed to evidence {evidence_id}")
        try:
            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"data: {data}\n\n"
                    # Stop streaming once terminal state reached
                    parsed = json.loads(data)
                    if parsed.get("status") in ("parsed", "failed"):
                        break
                except asyncio.TimeoutError:
                    # Send a keep-alive comment so the connection stays open
                    yield ": keep-alive\n\n"
        finally:
            try:
                _channels[evidence_id].remove(q)
            except ValueError:
                pass
            logger.debug(f"[EventStream] Client unsubscribed from evidence {evidence_id}")
