"""
Correlations API — ForenSight AI
"""
import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId

from backend.app.services.graph.graph_queries import GraphCorrelationRules
from backend.app.repositories.case_repository import CaseRepository
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.rbac import require_investigator, require_viewer
from backend.app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["correlations"])


@router.get("/cases/{case_id}/correlations", response_model=Dict[str, Any])
async def get_case_correlations(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Viewer+ can read correlations."""
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
        return await GraphCorrelationRules.get_correlation_summary(case_id, current_user.organization_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j error: {e}")


@router.post("/cases/{case_id}/correlations/run", response_model=Dict[str, Any])
async def run_case_correlations(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Investigator+ can re-run correlation rules."""
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
        results = await GraphCorrelationRules.run_all_rules(case_id, current_user.organization_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j error: {e}")

    await AuditRepository.log(
        actor_id=current_user.id, org_id=current_user.organization_id,
        action="correlations.run", entity_type="case", entity_id=case_id,
        metadata={"results": {k: str(v) for k, v in results.items()}},
    )
    return {"case_id": case_id, "rules_applied": results}
