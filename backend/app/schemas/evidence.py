from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class EvidenceType(str, Enum):
    EVTX           = "evtx"
    PCAP           = "pcap"
    BROWSER_SQLITE = "browser_sqlite"
    CSV            = "csv"
    JSON           = "json"
    TEXT           = "text"

class EvidenceStatus(str, Enum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PARSING = "parsing"
    PARSED = "parsed"
    FAILED = "failed"

class EvidenceBase(BaseModel):
    filename: str = Field(..., description="Original name of the uploaded forensic file")
    file_type: EvidenceType = Field(..., description="Identified format of the evidence")
    size_bytes: int = Field(..., description="File size in bytes")

class EvidenceCreate(EvidenceBase):
    case_id: str = Field(..., description="Case ID this evidence is attached to")
    sha256: str = Field(..., description="SHA-256 hash for chain of custody & integrity checks")
    minio_object_name: str = Field(..., description="Internal object storage reference name")

class EvidenceUpdateStatus(BaseModel):
    status: EvidenceStatus = Field(..., description="New parsing stage status")
    error_message: Optional[str] = Field(None, description="Detailed parser failure reason, if any")

class EvidenceResponse(EvidenceBase):
    id: str = Field(..., description="The evidence's MongoDB ObjectId representation")
    case_id: str = Field(..., description="The parent case ID")
    organization_id: str = Field(..., description="The owner organization ID")
    sha256: str = Field(..., description="SHA-256 hash")
    minio_object_name: str = Field(..., description="Internal storage object identifier")
    status: EvidenceStatus
    error_message: Optional[str] = None
    parsing_started_at: Optional[datetime] = None
    parsed_at: Optional[datetime] = None
    created_by: str = Field(..., description="The User ID who uploaded the file")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "60c72b2f9b1d8b2a5c8b4570",
                "case_id": "60c72b2f9b1d8b2a5c8b4569",
                "organization_id": "60c72b2f9b1d8b2a5c8b4567",
                "filename": "Security.evtx",
                "file_type": "evtx",
                "size_bytes": 10485760,
                "sha256": "4e38e68cf0cf5b2c938153c3d526ad0b1f1489e32ad4e0db2c9182390f7a20c3",
                "minio_object_name": "org1/case1/4e38e68cf0cf5b2c938153c3d526ad0b1f1489e32ad4e0db2c9182390f7a20c3.evtx",
                "status": "parsed",
                "error_message": None,
                "created_by": "60c72b2f9b1d8b2a5c8b4568",
                "created_at": "2026-07-10T12:10:00Z",
                "updated_at": "2026-07-10T12:12:00Z"
            }
        }
