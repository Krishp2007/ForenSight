from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
import logging
from typing import Dict, Any

from backend.app.repositories.graph_repository import GraphRepository
from backend.app.repositories.case_repository import CaseRepository
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["graph"])

@router.get("/cases/{case_id}/graph", response_model=Dict[str, Any])
async def get_case_graph(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve Neo4j node-link visualization data for a case."""
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    from backend.app.db.neo4j import neo4j_client
    if not neo4j_client.driver:
        raise HTTPException(status_code=503, detail="Graph database (Neo4j) is not available. Start Neo4j and re-parse evidence.")

    try:
        graph_data = await GraphRepository.get_case_graph(case_id, current_user.organization_id)
    except Exception as e:
        logger.error(f"Graph fetch failed: {e}")
        raise HTTPException(status_code=503, detail=f"Neo4j error: {e}")
    return graph_data


@router.get("/cases/{case_id}/graph/analytics", response_model=Dict[str, Any])
async def get_case_graph_analytics(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    from backend.app.db.neo4j import neo4j_client
    if not neo4j_client.driver:
        raise HTTPException(status_code=503, detail="Neo4j is not available.")

    try:
        from backend.app.services.graph.graph_analytics import GraphAnalytics
        summary = await GraphAnalytics.full_summary(case_id, current_user.organization_id)
    except Exception as e:
        logger.error(f"Graph analytics failed: {e}")
        raise HTTPException(status_code=503, detail=f"Neo4j error: {e}")
    return summary

@router.post("/cases/{case_id}/graph/sync", response_model=Dict[str, Any])
async def sync_case_graph(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Re-sync all parsed events from MongoDB into Neo4j for this case.
    Use this if the graph is empty after parsing (e.g. Neo4j was down during parse).
    """
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    from backend.app.db.neo4j import neo4j_client
    if not neo4j_client.driver:
        raise HTTPException(status_code=503, detail="Neo4j is not available.")

    try:
        from backend.app.repositories.event_repository import EventRepository
        events = await EventRepository.list_by_case(case_id, current_user.organization_id, limit=10000)
        if not events:
            return {"synced": 0, "detail": "No events found in MongoDB for this case."}
        synced = await GraphRepository.bulk_import_events(events)
        return {"synced": synced, "total_events": len(events)}
    except Exception as e:
        logger.error(f"Graph sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {e}")
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

    # Audit log
    await AuditRepository.log(
        actor_id=current_user.id,
        org_id=current_user.organization_id,
        action="graph.clear",
        entity_type="case",
        entity_id=case_id,
    )
    return None
