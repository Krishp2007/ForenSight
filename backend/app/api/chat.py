from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
import logging
from typing import Optional
from pydantic import BaseModel

from backend.app.services.ai.copilot import CopilotService
from backend.app.repositories.case_repository import CaseRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["copilot"])

class CopilotQuery(BaseModel):
    question: Optional[str] = None

class CopilotResponse(BaseModel):
    analysis: str

@router.post("/cases/{case_id}/copilot", response_model=CopilotResponse)
async def ask_copilot(
    case_id: str,
    query: CopilotQuery,
    current_user: UserResponse = Depends(get_current_user)
):
    """Ask Antigravity Copilot a question or request a summary audit report of the case context."""
    if not ObjectId.is_valid(case_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid case ID format"
        )
        
    # Enforce tenant isolation boundaries
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or access denied"
        )
        
    try:
        report_text = await CopilotService.analyze_case_timeline(
            case_id=case_id,
            org_id=current_user.organization_id,
            question=query.question
        )
        return CopilotResponse(analysis=report_text)
    except Exception as e:
        logger.error(f"AI Copilot generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Copilot analysis model failed: {str(e)}"
        )
