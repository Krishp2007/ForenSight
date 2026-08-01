from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.organization import OrganizationCreate, OrganizationResponse
from backend.app.repositories.organization_repository import OrganizationRepository

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(payload: OrganizationCreate):
    """Create a new tenant organization."""
    existing_org = await OrganizationRepository.get_by_name(payload.name)
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this name already exists"
        )
    
    now = datetime.utcnow()
    org_dict = {
        "name": payload.name,
        "created_at": now,
        "updated_at": now
    }
    
    created_org = await OrganizationRepository.create(org_dict)
    # Map MongoDB document to Response schema
    created_org["id"] = str(created_org["_id"])
    return created_org

@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations():
    """List all organizations — public endpoint used during user registration."""
    orgs = await OrganizationRepository.list_all()
    response_orgs = []
    for org in orgs:
        org["id"] = str(org["_id"])
        response_orgs.append(org)
    return response_orgs
