"""
Event Stream — ForenSight AI (Lightweight Module)
=====================================================
Stream status updates during evidence ingestion.
"""

import logging
from typing import Any, AsyncIterator, Dict

logger = logging.getLogger(__name__)


class EventStream:
    @classmethod
    def publish(cls, evidence_id: str, status: str, progress: int = 0, message: str = "", extra: Dict[str, Any] | None = None) -> None:
        pass

    @classmethod
    async def subscribe(cls, evidence_id: str) -> AsyncIterator[str]:
        yield f'data: {{"evidence_id": "{evidence_id}", "status": "parsed"}}\n\n'
