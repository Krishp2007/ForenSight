from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
import logging
from typing import Dict, Any

from backend.app.repositories.graph_repository import GraphRepository
from backend.app.repositories.case_repository import CaseRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["graph"])

@router.get("/cases/{case_id}/graph", response_model=Dict[str, Any])
async def get_case_graph(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve Neo4j node-link visualization representation for a specific case timeline."""
    # 1. Validate ID format
    if not ObjectId.is_valid(case_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid case ID format"
        )
        
    # 2. Verify case tenant boundaries
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or access denied"
        )
        
    # 3. Retrieve graph dataset
    graph_data = await GraphRepository.get_case_graph(case_id, current_user.organization_id)
    return graph_data

@router.delete("/cases/{case_id}/graph", status_code=status.HTTP_204_NO_CONTENT)
async def clear_case_graph(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Clear Neo4j graph nodes and relationships for a case."""
    # 1. Validate ID format
    if not ObjectId.is_valid(case_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid case ID format"
        )
        
    # 2. Verify case tenant boundaries
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or access denied"
        )
        
    # 3. Clear graph
    await GraphRepository.clear_case_graph(case_id, current_user.organization_id)
    return None
