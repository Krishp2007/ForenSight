"""
Users API — ForenSight AI
===========================
Admin-only endpoints for managing users within an organization.
  GET    /users           — list all org users
  PATCH  /users/:id       — update role / active status
  DELETE /users/:id       — deactivate a user
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from pydantic import BaseModel

from backend.app.repositories.user_repository import UserRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.rbac import require_admin
from backend.app.schemas.user import UserResponse, UserRole

router = APIRouter(tags=["users"])


class UserAdminUpdate(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


def _fmt(u: dict) -> dict:
    u["id"] = str(u["_id"])
    u["organization_id"] = str(u["organization_id"])
    u.pop("_id", None)
    u.pop("hashed_password", None)
    return u


@router.get("/users", response_model=List[Dict[str, Any]])
async def list_org_users(
    current_user: UserResponse = Depends(get_current_user),
):
    """Admin only — list all users in the organization."""
    require_admin(current_user.role)
    users = await UserRepository.list_by_org(current_user.organization_id)
    return [_fmt(u) for u in users]


@router.patch("/users/{user_id}", response_model=Dict[str, Any])
async def update_user(
    user_id: str,
    payload: UserAdminUpdate,
    current_user: UserResponse = Depends(get_current_user),
):
    """Admin only — change a user's role or active status."""
    require_admin(current_user.role)
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own account via admin endpoint.")

    target = await UserRepository.get_by_id(user_id)
    if not target or str(target["organization_id"]) != current_user.organization_id:
        raise HTTPException(status_code=404, detail="User not found in your organization.")

    fields: dict = {"updated_at": datetime.utcnow()}
    if payload.role is not None:
        fields["role"] = payload.role.value
    if payload.is_active is not None:
        fields["is_active"] = payload.is_active

    if len(fields) == 1:
        raise HTTPException(status_code=400, detail="No fields to update.")

    updated = await UserRepository.update(user_id, fields)
    if not updated:
        raise HTTPException(status_code=500, detail="Update failed.")
    return _fmt(updated)


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Admin only — deactivate (soft-delete) a user."""
    require_admin(current_user.role)
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account.")

    target = await UserRepository.get_by_id(user_id)
    if not target or str(target["organization_id"]) != current_user.organization_id:
        raise HTTPException(status_code=404, detail="User not found in your organization.")

    await UserRepository.update(user_id, {"is_active": False, "updated_at": datetime.utcnow()})
    return {"detail": f"User {user_id} deactivated."}
