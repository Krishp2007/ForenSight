"""
Correlations API — ForenSight AI
==================================
Exposes the three Cypher correlation rules via REST:
  - GET  /cases/:id/correlations         — fetch derived correlations from graph
  - POST /cases/:id/correlations/run     — manually re-trigger all 3 rules

Architecture Section 5.5.1: rule-based correlation, Cypher queries.
"""

import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId

from backend.app.services.graph.graph_queries import GraphCorrelationRules
from backend.app.repositories.case_repository import CaseRepository
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["correlations"])


@router.get("/cases/{case_id}/correlations", response_model=Dict[str, Any])
async def get_case_correlations(
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
        raise HTTPException(status_code=503, detail="Graph database (Neo4j) is not available. Start Neo4j to use correlations.")

    try:
        summary = await GraphCorrelationRules.get_correlation_summary(
            case_id, current_user.organization_id
        )
    except Exception as e:
        logger.error(f"Correlations fetch failed: {e}")
        raise HTTPException(status_code=503, detail=f"Neo4j error: {e}")
    return summary


@router.post("/cases/{case_id}/correlations/run", response_model=Dict[str, Any])
async def run_case_correlations(
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
        raise HTTPException(status_code=503, detail="Graph database (Neo4j) is not available. Start Neo4j to run correlations.")

    try:
        results = await GraphCorrelationRules.run_all_rules(
            case_id, current_user.organization_id
        )
    except Exception as e:
        logger.error(f"Correlations run failed: {e}")
        raise HTTPException(status_code=503, detail=f"Neo4j error: {e}")

    await AuditRepository.log(
        actor_id=current_user.id,
        org_id=current_user.organization_id,
        action="correlations.run",
        entity_type="case",
        entity_id=case_id,
        metadata={"results": {k: str(v) for k, v in results.items()}},
    )
    return {"case_id": case_id, "rules_applied": results}
