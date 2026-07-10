from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class CaseStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    SUSPENDED = "suspended"
    RESOLVED = "resolved"

class CaseBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=150, description="Title of the digital forensics case")
    description: Optional[str] = Field(None, description="Detailed explanation of case scope, system, or incident details")
    status: CaseStatus = Field(default=CaseStatus.OPEN, description="Current investigation status")

class CaseCreate(CaseBase):
    pass

class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = None
    status: Optional[CaseStatus] = None

class CaseResponse(CaseBase):
    id: str = Field(..., description="The case's MongoDB ObjectId representation")
    organization_id: str = Field(..., description="The organization ID this case belongs to")
    created_by: str = Field(..., description="The User ID of the creator")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "60c72b2f9b1d8b2a5c8b4569",
                "title": "APT29 Phishing Investigation",
                "description": "Investigating email execution of malicious payloads on Finance workstations",
                "status": "in_progress",
                "organization_id": "60c72b2f9b1d8b2a5c8b4567",
                "created_by": "60c72b2f9b1d8b2a5c8b4568",
                "created_at": "2026-07-10T12:00:00Z",
                "updated_at": "2026-07-10T12:15:00Z"
            }
        }
