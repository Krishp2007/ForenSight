from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="The name of the organization")

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)

class OrganizationResponse(OrganizationBase):
    id: str = Field(..., description="The hex string representation of MongoDB ObjectId")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "60c72b2f9b1d8b2a5c8b4567",
                "name": "ForenSight Security Lab",
                "created_at": "2026-07-10T12:00:00Z",
                "updated_at": "2026-07-10T12:00:00Z"
            }
        }
