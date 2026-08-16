from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from backend.app.schemas.user import UserRole

class InviteCreate(BaseModel):
    role: UserRole = Field(default=UserRole.INVESTIGATOR, description="Role assigned upon joining")
    target_email: Optional[EmailStr] = Field(None, description="Optional target email address to restrict invite to")
    expires_in_days: int = Field(default=7, ge=1, le=30, description="Validity period in days")

class InviteResponse(BaseModel):
    id: str
    token: str
    invite_url: str
    organization_id: str
    organization_name: str
    role: UserRole
    target_email: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    is_used: bool

class InviteValidateResponse(BaseModel):
    valid: bool
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    role: Optional[UserRole] = None
    target_email: Optional[str] = None
    error: Optional[str] = None
