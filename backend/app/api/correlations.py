"""
Correlations API — ForenSight
===============================
Provides REST endpoints for fetching and re-running graph correlation findings.
"""

import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId

from backend.app.services.graph.graph_correlation import GraphCorrelationEngine
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
    """Retrieve detected graph correlations and score summary for a case. Viewer+"""
    require_viewer(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    try:
        return await GraphCorrelationEngine.get_all_case_correlations(case_id)
    except Exception as e:
        logger.error(f"Correlations fetch failed: {e}")
        raise HTTPException(status_code=503, detail=f"Neo4j error: {e}")


@router.post("/cases/{case_id}/correlations/run", response_model=Dict[str, Any])
async def run_case_correlations(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Re-run forensic correlation engine against Neo4j case graph. Investigator+"""
    require_investigator(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    try:
        results = await GraphCorrelationEngine.get_all_case_correlations(case_id)
    except Exception as e:
        logger.error(f"Correlation execution failed: {e}")
        raise HTTPException(status_code=503, detail=f"Neo4j error: {e}")

    await AuditRepository.log(
        actor_id=current_user.id,
        org_id=current_user.organization_id,
        action="correlations.run",
        entity_type="case",
        entity_id=case_id,
        metadata={"total": results.get("total_correlations", 0)},
    )
    return results
