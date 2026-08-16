from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from bson import ObjectId

from backend.app.config import settings
from backend.app.schemas.user import UserResponse, UserRole
from backend.app.schemas.invite import InviteCreate, InviteResponse, InviteValidateResponse
from backend.app.repositories.invite_repository import InviteRepository
from backend.app.repositories.organization_repository import OrganizationRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.rbac import require_admin

router = APIRouter(prefix="/invites", tags=["invites"])

def _format_invite_response(invite: dict, org_name: str) -> dict:
    invite_id = str(invite["_id"])
    token = invite["token"]
    org_id = str(invite["organization_id"])
    frontend_base = getattr(settings, "FRONTEND_URL", "http://localhost:5173").rstrip("/")
    invite_url = f"{frontend_base}/register?invite={token}"
    
    return {
        "id": invite_id,
        "token": token,
        "invite_url": invite_url,
        "organization_id": org_id,
        "organization_name": org_name,
        "role": invite["role"],
        "target_email": invite.get("target_email"),
        "created_at": invite["created_at"],
        "expires_at": invite["expires_at"],
        "is_used": invite.get("is_used", False),
    }

@router.post("", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    payload: InviteCreate,
    current_user: UserResponse = Depends(get_current_user),
):
    """Admin only — generate a shareable organization invite link."""
    require_admin(current_user.role)

    org = await OrganizationRepository.get_by_id(current_user.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    created = await InviteRepository.create_invite(
        organization_id=current_user.organization_id,
        role=payload.role.value,
        created_by=current_user.id,
        target_email=payload.target_email,
        expires_in_days=payload.expires_in_days
    )

    org_name = org.get("name", "ForenSight Security")
    return _format_invite_response(created, org_name)

@router.get("", response_model=List[InviteResponse])
@router.get("/", response_model=List[InviteResponse])
async def list_org_invites(
    current_user: UserResponse = Depends(get_current_user),
):
    """Admin only — list all active and historical invites for the organization."""
    require_admin(current_user.role)

    org = await OrganizationRepository.get_by_id(current_user.organization_id)
    org_name = org.get("name", "ForenSight Security") if org else "ForenSight Security"

    invites = await InviteRepository.list_by_org(current_user.organization_id)
    return [_format_invite_response(inv, org_name) for inv in invites]

@router.delete("/{invite_id}", status_code=status.HTTP_200_OK)
async def revoke_invite(
    invite_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Admin only — revoke an active invite token."""
    require_admin(current_user.role)

    success = await InviteRepository.revoke_invite(invite_id, current_user.organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite token not found or already used/revoked."
        )
    return {"message": "Invite token revoked successfully."}

@router.get("/validate", response_model=InviteValidateResponse)
async def validate_invite(token: str = Query(..., min_length=10)):
    """Public endpoint — validate an invite token and return pre-assigned organization and role."""
    invite = await InviteRepository.get_valid_invite(token)
    if not invite:
        return InviteValidateResponse(
            valid=False,
            error="Invite link is invalid, expired, or has already been used. Please ask your administrator for a new invite link."
        )

    org_id = str(invite["organization_id"])
    org = await OrganizationRepository.get_by_id(org_id)
    if not org:
        return InviteValidateResponse(
            valid=False,
            error="Associated organization no longer exists."
        )

    return InviteValidateResponse(
        valid=True,
        organization_id=org_id,
        organization_name=org.get("name", "ForenSight Security"),
        role=UserRole(invite["role"]),
        target_email=invite.get("target_email")
    )
