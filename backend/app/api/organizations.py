from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.organization import OrganizationCreate, OrganizationResponse
from backend.app.repositories.organization_repository import OrganizationRepository

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(payload: OrganizationCreate):
    """Create a new tenant organization."""
    try:
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
        org_id = str(created_org["_id"])
        created_org["id"] = org_id

        # Generate initial Admin invite token for agency founder
        from backend.app.repositories.invite_repository import InviteRepository
        from backend.app.config import settings
        invite_record = await InviteRepository.create_invite(
            organization_id=org_id,
            role="admin",
            expires_in_days=3
        )

        frontend_base = getattr(settings, "FRONTEND_URL", "http://localhost:5173").rstrip("/")
        created_org["admin_invite_token"] = invite_record["token"]
        created_org["admin_invite_url"] = f"{frontend_base}/register?invite={invite_record['token']}"
        return created_org
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: Unable to connect to MongoDB ({str(err)})"
        )

@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations():
    """List all organizations — public endpoint used during user registration."""
    try:
        orgs = await OrganizationRepository.list_all()
        response_orgs = []
        for org in orgs:
            org["id"] = str(org["_id"])
            response_orgs.append(org)
        return response_orgs
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(err)}"
        )

