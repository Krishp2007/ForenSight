"""
Audit Log API — ForenSight AI
==============================
Exposes the append-only Merkle audit trail for cases and organizations.
Also exposes the chain-integrity verification endpoint.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId

from backend.app.repositories.audit_repository import AuditRepository
from backend.app.repositories.case_repository import CaseRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.user import UserResponse

router = APIRouter(tags=["audit"])


@router.get("/cases/{case_id}/audit", response_model=List[Dict[str, Any]])
async def get_case_audit_log(
    case_id: str,
    limit: int = 200,
    current_user: UserResponse = Depends(get_current_user),
):
    """Return the full append-only audit trail for a specific case (chronological order)."""
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")

    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    rows = await AuditRepository.list_for_case(case_id, current_user.organization_id, limit=limit)
    return rows


@router.get("/audit", response_model=List[Dict[str, Any]])
async def get_org_audit_log(
    limit: int = 500,
    current_user: UserResponse = Depends(get_current_user),
):
    """Return the most recent audit entries across all cases for the organization."""
    rows = await AuditRepository.list_for_org(current_user.organization_id, limit=limit)
    return rows


@router.get("/audit/verify", response_model=Dict[str, Any])
async def verify_audit_chain(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Walk the full audit chain for the organization and verify Merkle hash integrity.
    Returns { valid, total, broken_at, broken_id }.
    A valid=true result proves no rows have been tampered with.
    """
    result = await AuditRepository.verify_chain(current_user.organization_id)
    return result
