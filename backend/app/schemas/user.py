from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserRole(str, Enum):
    ADMIN = "admin"
    INVESTIGATOR = "investigator"
    VIEWER = "viewer"

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Unique email address of the user")
    username: str = Field(..., min_length=3, max_length=50, description="Username of the investigator")
    organization_id: str = Field(..., description="MongoDB Organization ID this user belongs to")
    role: UserRole = Field(default=UserRole.INVESTIGATOR, description="Access role for RBAC")
    is_active: bool = Field(default=True, description="Whether this account is active")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Plaintext password (hashed before storing)")

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)

class UserResponse(UserBase):
    id: str = Field(..., description="The user's MongoDB ObjectId representation")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "60c72b2f9b1d8b2a5c8b4568",
                "email": "analyst@forensight.org",
                "username": "investigator_alice",
                "organization_id": "60c72b2f9b1d8b2a5c8b4567",
                "role": "investigator",
                "is_active": True,
                "created_at": "2026-07-10T12:00:00Z",
                "updated_at": "2026-07-10T12:00:00Z"
            }
        }

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    role: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="The registered email address to send password reset link")

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token received via email")
    new_password: str = Field(..., min_length=8, description="New account password")

