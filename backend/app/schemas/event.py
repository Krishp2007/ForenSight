from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class EventSource(str, Enum):
    EVTX    = "evtx"
    PCAP    = "pcap"
    BROWSER = "browser"
    CSV     = "csv"
    JSON    = "json"
    TEXT    = "text"

class EventType(str, Enum):
    PROCESS_CREATION   = "process_creation"
    NETWORK_CONNECTION = "network_connection"
    FILE_MODIFICATION  = "file_modification"
    REGISTRY_CHANGE    = "registry_change"
    AUTH_EVENT         = "auth_event"
    BROWSER_HISTORY    = "browser_history"
    BROWSER_DOWNLOAD   = "browser_download"
    BROWSER_CREDENTIAL = "browser_credential"
    HASH_RECORD        = "hash_record"
    CSV                = "csv"
    JSON               = "json"
    GENERIC            = "generic"

class EventSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EventBase(BaseModel):
    timestamp: datetime = Field(..., description="Chronological time the activity occurred")
    event_type: str = Field(..., description="Normalized action category (e.g. process_creation)")
    source: str = Field(default="generic", description="Parser category of raw evidence")
    severity: str = Field(default="info", description="Calculated finding severity")
    
    # Semantic Subject-Action-Object triple for graph building
    subject: str = Field(default="System", description="The actor initiating action (e.g. 'cmd.exe', 'SYSTEM', 'UserA')")
    action: str = Field(default="activity", description="Specific action executed (e.g. 'spawned', 'connected_to', 'deleted')")
    object: str = Field(default="event", description="The target entity of the action (e.g. 'powershell.exe', '192.168.1.5', 'registry_key')")
    
    # Custom attributes from the raw parser
    details: Dict[str, Any] = Field(default_factory=dict, description="Raw key-value details from parser (e.g. PID, CommandLine, SourcePort)")
    
    # Threat Intelligence & Analytics metadata
    description: Optional[str] = Field(default=None, description="Plain English sentence explaining the event for investigators")
    mitre_techniques: List[str] = Field(default_factory=list, description="Mapped MITRE ATT&CK technique IDs (e.g. ['T1059.001'])")
    is_anomaly: bool = Field(default=False, description="Flagged as outlier by local ML engines")
    anomaly_score: float = Field(default=0.0, description="Outlying probability score between 0.0 and 1.0")
    processed_at: Optional[datetime] = Field(default=None, description="Timestamp when evidence processing completed")

class EventCreate(EventBase):
    case_id: str = Field(..., description="Parent case ID")
    evidence_id: str = Field(..., description="Originating evidence file ID")

class EventUpdate(BaseModel):
    severity: Optional[EventSeverity] = None
    mitre_techniques: Optional[List[str]] = None
    is_anomaly: Optional[bool] = None
    anomaly_score: Optional[float] = None

class EventResponse(EventBase):
    id: str = Field(..., description="The event's MongoDB ObjectId representation")
    case_id: str = Field(..., description="Parent case ID")
    evidence_id: str = Field(..., description="Originating evidence ID")
    organization_id: str = Field(..., description="Owner organization ID")

    # Optional semantic search rank properties
    distance: Optional[float] = Field(default=None, description="FAISS L2 search match distance")
    search_sentence: Optional[str] = Field(default=None, description="Formatted sentence used for vector embedding matching")

    class Config:
        from_attributes = True
        extra = 'ignore'  # ignore unknown MongoDB fields like _id, processed_at etc.
        json_schema_extra = {
            "example": {
                "id": "60c72b2f9b1d8b2a5c8b4571",
                "case_id": "60c72b2f9b1d8b2a5c8b4569",
                "evidence_id": "60c72b2f9b1d8b2a5c8b4570",
                "organization_id": "60c72b2f9b1d8b2a5c8b4567",
                "timestamp": "2026-07-10T12:05:32Z",
                "event_type": "process_creation",
                "source": "evtx",
                "severity": "medium",
                "subject": "explorer.exe (PID: 3420)",
                "action": "spawned",
                "object": "powershell.exe -ExecutionPolicy Bypass -File C:\\tmp\\payload.ps1 (PID: 5124)",
                "details": {
                    "ParentProcessId": 3420,
                    "ProcessId": 5124,
                    "CommandLine": "powershell.exe -ExecutionPolicy Bypass -File C:\\tmp\\payload.ps1",
                    "User": "Workstation01\\LocalUser"
                },
                "mitre_techniques": ["T1059.001"],
                "is_anomaly": True,
                "anomaly_score": 0.82
            }
        }

class PaginatedEventResponse(BaseModel):
    events: List[EventResponse] = Field(..., description="List of events on the current page")
    total: int = Field(..., description="Uncapped total matching events count")
    page: int = Field(..., description="Current page number (1-indexed)")
    limit: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total pages available")

