from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from backend.app.schemas.case import CaseCreate, CaseUpdate, CaseResponse, CaseStatus
from backend.app.repositories.case_repository import CaseRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.rbac import require_investigator, require_admin, require_viewer
from backend.app.schemas.user import UserResponse
from backend.app.repositories.audit_repository import AuditRepository
from bson import ObjectId

router = APIRouter(prefix="/cases", tags=["cases"])

@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new forensic case container (requires Investigator/Admin privileges)."""
    # Enforce RBAC
    require_investigator(current_user.role)
    
    now = datetime.utcnow()
    case_dict = {
        "organization_id": ObjectId(current_user.organization_id),
        "title": payload.title,
        "description": payload.description,
        "status": payload.status.value,
        "created_by": ObjectId(current_user.id),
        "created_at": now,
        "updated_at": now
    }
    
    created_case = await CaseRepository.create(case_dict)
    
    # Map MongoDB fields
    created_case["id"] = str(created_case["_id"])
    created_case["organization_id"] = str(created_case["organization_id"])
    created_case["created_by"] = str(created_case["created_by"])

    # Append-only audit log entry
    await AuditRepository.log(
        actor_id=current_user.id,
        org_id=current_user.organization_id,
        action="case.create",
        entity_type="case",
        entity_id=created_case["id"],
        metadata={"title": payload.title, "status": payload.status.value},
    )
    return created_case

@router.get("", response_model=List[CaseResponse])
@router.get("/", response_model=List[CaseResponse])
async def list_cases(
    status_filter: Optional[CaseStatus] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """List all cases scoped under the authenticated user's organization."""
    require_viewer(current_user.role)
    cases = await CaseRepository.list_by_org(
        org_id=current_user.organization_id,
        status=status_filter.value if status_filter else None
    )
    
    response_cases = []
    for c in cases:
        c["id"] = str(c["_id"])
        c["organization_id"] = str(c["organization_id"])
        c["created_by"] = str(c["created_by"])
        response_cases.append(c)
    return response_cases

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case_details(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Fetch detail specifications of a case by its ID."""
    require_viewer(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid case ID format"
        )
        
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or access denied"
        )
        
    case["id"] = str(case["_id"])
    case["organization_id"] = str(case["organization_id"])
    case["created_by"] = str(case["created_by"])
    return case

@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: str,
    payload: CaseUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update case status or description (requires Investigator/Admin privileges)."""
    # Enforce RBAC
    require_investigator(current_user.role)
    
    if not ObjectId.is_valid(case_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid case ID format"
        )
        
    # Build dynamic update payload
    update_data = {}
    if payload.title is not None:
        update_data["title"] = payload.title
    if payload.description is not None:
        update_data["description"] = payload.description
    if payload.status is not None:
        update_data["status"] = payload.status.value
        
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update parameters provided"
        )
        
    update_data["updated_at"] = datetime.utcnow()
    
    updated_case = await CaseRepository.update(
        case_id=case_id,
        org_id=current_user.organization_id,
        update_data=update_data
    )
    
    if not updated_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or access denied"
        )
        
    updated_case["id"] = str(updated_case["_id"])
    updated_case["organization_id"] = str(updated_case["organization_id"])
    updated_case["created_by"] = str(updated_case["created_by"])

    # Append-only audit log entry
    await AuditRepository.log(
        actor_id=current_user.id,
        org_id=current_user.organization_id,
        action="case.update",
        entity_type="case",
        entity_id=case_id,
        metadata=update_data,
    )
    return updated_case
