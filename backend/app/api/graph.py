from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
import logging
from typing import Dict, Any

from backend.app.repositories.graph_repository import GraphRepository
from backend.app.repositories.case_repository import CaseRepository
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.rbac import require_investigator, require_viewer
from backend.app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["graph"])


@router.get("/cases/{case_id}/graph", response_model=Dict[str, Any])
async def get_case_graph(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Retrieve Neo4j node-link visualization data for a case. Viewer+"""
    require_viewer(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    from backend.app.db.neo4j import neo4j_client
    if not neo4j_client.driver:
        raise HTTPException(status_code=503, detail="Graph database (Neo4j) is not available. Start Neo4j and re-parse evidence.")
    try:
        return await GraphRepository.get_case_graph(case_id, current_user.organization_id)
    except Exception as e:
        logger.error(f"Graph fetch failed: {e}")
        raise HTTPException(status_code=503, detail=f"Neo4j error: {e}")


@router.get("/cases/{case_id}/graph/analytics", response_model=Dict[str, Any])
async def get_case_graph_analytics(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Graph structural analytics. Viewer+"""
    require_viewer(current_user.role)
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
        return await GraphAnalytics.full_summary(case_id, current_user.organization_id)
    except Exception as e:
        logger.error(f"Graph analytics failed: {e}")
        raise HTTPException(status_code=503, detail=f"Neo4j error: {e}")


@router.post("/cases/{case_id}/graph/sync", response_model=Dict[str, Any])
async def sync_case_graph(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Push MongoDB events → Neo4j. Investigator+"""
    require_investigator(current_user.role)
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


@router.delete("/cases/{case_id}/graph", status_code=status.HTTP_204_NO_CONTENT)
async def clear_case_graph(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Clear Neo4j graph nodes and relationships for a case. Investigator+"""
    require_investigator(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    await GraphRepository.clear_case_graph(case_id, current_user.organization_id)
    await AuditRepository.log(
        actor_id=current_user.id,
        org_id=current_user.organization_id,
        action="graph.clear",
        entity_type="case",
        entity_id=case_id,
    )
    return None
