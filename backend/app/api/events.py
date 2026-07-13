from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
import logging

from backend.app.schemas.event import EventResponse, EventSeverity, EventType
from backend.app.repositories.event_repository import EventRepository
from backend.app.repositories.case_repository import CaseRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["events"])

@router.get("/cases/{case_id}/events", response_model=List[EventResponse])
async def list_case_events(
    case_id: str,
    severity: Optional[EventSeverity] = None,
    event_type: Optional[EventType] = None,
    limit: int = 100,
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve normalized forensic timeline events for a specific case (scopes by organization)."""
    # 1. Validate ID formats
    if not ObjectId.is_valid(case_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid case ID format"
        )
        
    # 2. Enforce tenant organization boundaries (check case existence)
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or access denied"
        )
        
    # 3. Query events list using Repository
    sev_val = severity.value if severity else None
    type_val = event_type.value if event_type else None
    
    # Restrict maximum limit to safeguard database performance
    query_limit = min(limit, 2000)
    
    events = await EventRepository.list_by_case(
        case_id=case_id,
        org_id=current_user.organization_id,
        severity=sev_val,
        event_type=type_val,
        limit=query_limit
    )
    
    # 4. Map MongoDB documents to EventResponse Pydantic structures
    responses = []
    for event in events:
        event["id"] = str(event["_id"])
        event["case_id"] = str(event["case_id"])
        event["evidence_id"] = str(event["evidence_id"])
        event["organization_id"] = str(event["organization_id"])
        responses.append(EventResponse(**event))
        
    return responses
