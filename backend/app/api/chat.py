"""
Chat / Copilot API — ForenSight AI  (v2 — Streaming)
=====================================================
Endpoints:
  POST /cases/{case_id}/copilot           - Non-streaming (backward compatible)
  GET  /cases/{case_id}/copilot/stream    - SSE streaming (new)
  GET  /cases/{case_id}/copilot/history   - Load stored chat history
  DELETE /cases/{case_id}/copilot/history - Clear chat history
"""

import json
import logging
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.rbac import require_viewer
from backend.app.repositories.case_repository import CaseRepository
from backend.app.schemas.user import UserResponse
from backend.app.services.ai.copilot import CopilotService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["copilot"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class CopilotQuery(BaseModel):
    question: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None


class CopilotResponse(BaseModel):
    analysis: str
    confidence: str = "High"
    sources: Optional[List[Dict[str, Any]]] = None


# ── Non-streaming (backward-compatible) ──────────────────────────────────────
@router.post("/cases/{case_id}/copilot", response_model=CopilotResponse)
async def ask_copilot(
    case_id: str,
    query: CopilotQuery,
    current_user: UserResponse = Depends(get_current_user),
):
    """Viewer+ can use the AI copilot (non-streaming, backward compatible)."""
    require_viewer(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")
    try:
        res = await CopilotService.analyze_case_timeline(
            case_id=case_id,
            org_id=current_user.organization_id,
            question=query.question,
            history=query.history,
        )
        if isinstance(res, dict):
            return CopilotResponse(
                analysis=res.get("analysis", ""),
                confidence=res.get("confidence", "High"),
                sources=res.get("sources", []),
            )
        return CopilotResponse(analysis=str(res), confidence="High", sources=[])
    except Exception as e:
        logger.error(f"[Copilot] Non-streaming failed: {e}")
        raise HTTPException(status_code=500, detail="Copilot temporarily unavailable. Please try again.")


# ── SSE Streaming endpoint ────────────────────────────────────────────────────
@router.get("/cases/{case_id}/copilot/stream")
async def stream_copilot(
    case_id: str,
    question: str = Query(..., min_length=1, max_length=4000),
    history: Optional[str] = Query(None),  # JSON-encoded list
    current_user: UserResponse = Depends(get_current_user),
):
    """
    SSE streaming endpoint — yields tokens as they are generated.
    
    Event types:
      data: {"type": "token",   "content": "..."}
      data: {"type": "sources", "sources": [...]}
      data: {"type": "done",    "confidence": "High"}
      data: {"type": "error",   "content": "..."}
    """
    require_viewer(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    # Parse history from JSON query param
    parsed_history: List[Dict] = []
    if history:
        try:
            parsed_history = json.loads(history)
            if not isinstance(parsed_history, list):
                parsed_history = []
        except (json.JSONDecodeError, ValueError):
            parsed_history = []

    org_id = current_user.organization_id

    async def event_generator():
        """Async generator that yields SSE-formatted text chunks."""
        try:
            async for event in CopilotService.stream_response(
                case_id=case_id,
                org_id=org_id,
                question=question,
                history=parsed_history,
            ):
                payload = json.dumps(event, ensure_ascii=False)
                yield f"data: {payload}\n\n"
        except Exception as e:
            logger.error(f"[Copilot SSE] Unhandled error in stream: {e}")
            err = json.dumps({"type": "error", "content": "Sorry, I couldn't generate a response at this time. Please try again."})
            yield f"data: {err}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",      # Disable Nginx buffering
            "Connection": "keep-alive",
        },
    )


# ── Chat history endpoints ────────────────────────────────────────────────────
@router.get("/cases/{case_id}/copilot/history")
async def get_chat_history(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get the stored server-side chat history for a case (placeholder — client uses localStorage)."""
    require_viewer(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    # History is currently stored on the client (localStorage).
    # This endpoint exists for future server-side persistence.
    return {"case_id": case_id, "messages": []}


@router.delete("/cases/{case_id}/copilot/history")
async def clear_chat_history(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Clear server-side chat history for a case."""
    require_viewer(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    return {"case_id": case_id, "cleared": True}
