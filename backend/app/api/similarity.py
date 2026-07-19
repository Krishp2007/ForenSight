from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
import logging
from typing import List

from backend.app.services.ai.vector_store import VectorStore
from backend.app.repositories.case_repository import CaseRepository
from backend.app.schemas.event import EventResponse
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["similarity"])

@router.get("/cases/{case_id}/search", response_model=List[EventResponse])
async def search_events_semantically(
    case_id: str,
    query: str,
    limit: int = 10,
    current_user: UserResponse = Depends(get_current_user)
):
    """Perform natural language search against forensic case events using FAISS embeddings."""
    if not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )
        
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
        search_limit = min(limit, 100)
        results = await VectorStore.search_similar_events(
            case_id=case_id,
            org_id=current_user.organization_id,
            query=query,
            limit=search_limit
        )
        
        # Map DB docs to EventResponse pydantic models
        responses = []
        for doc in results:
            responses.append(EventResponse(**doc))
            
        return responses
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search index failed: {str(e)}"
        )
