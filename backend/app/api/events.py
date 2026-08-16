from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
import logging

from backend.app.schemas.event import EventResponse, EventSeverity, PaginatedEventResponse
from backend.app.repositories.event_repository import EventRepository
from backend.app.repositories.case_repository import CaseRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["events"])

def _generate_plain_english_description(event: dict) -> str:
    if event.get("description"):
        return event["description"]

    subj = event.get("subject", "System")
    act = str(event.get("action", "activity")).replace("_", " ")
    obj = event.get("object", "event")
    source = str(event.get("source") or "").lower()
    ev_type = str(event.get("event_type") or "").lower()
    details = event.get("details") or {}

    if source == "pcap" or "network" in ev_type:
        proto_code = details.get("proto_code")
        proto = "TCP" if proto_code == 6 else "UDP" if proto_code == 17 else "IP"
        length = f" ({details.get('length')} bytes)" if details.get("length") else ""
        dport = f" on port {details.get('dport')}" if details.get("dport") else ""
        return f"Host {subj} transmitted a {proto} packet{length} to destination {obj}{dport}."

    if "browser" in ev_type:
        title = details.get("title")
        if title:
            return f"User visited '{title}' via {subj}."
        return f"User visited link via {subj}."

    if "process" in ev_type:
        cmd = f" running command '{details.get('command_line')}'" if details.get("command_line") else ""
        return f"Process {subj} executed child process {obj}{cmd}."

    if "auth" in ev_type:
        return f"User {subj} performed {act} on target {obj}."

    return f"{subj} {act} {obj}."

@router.get("/cases/{case_id}/events", response_model=PaginatedEventResponse)
async def list_case_events(
    case_id: str,
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    search: Optional[str] = None,
    is_anomaly: Optional[bool] = None,
    sort_order: str = "desc",
    page: int = 1,
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve normalized, paginated forensic timeline events for a specific case with search and filters."""
    # 1. Validate ID formats
    if not ObjectId.is_valid(case_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid case ID format"
        )

    # 2. Enforce tenant organization boundaries (check case existence)
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or access denied"
        )

    # 3. Query events list using Repository
    res = await EventRepository.list_paginated_by_case(
        case_id=case_id,
        org_id=current_user.organization_id,
        severity=severity,
        event_type=event_type,
        search=search,
        is_anomaly=is_anomaly,
        sort_order=sort_order,
        page=page,
        limit=limit
    )

    # 4. Map MongoDB documents to EventResponse Pydantic structures
    responses = []
    for event in res["events"]:
        try:
            event["id"] = str(event["_id"])
            event["case_id"] = str(event.get("case_id", case_id))
            event["evidence_id"] = str(event.get("evidence_id", ""))
            event["organization_id"] = str(event.get("organization_id", current_user.organization_id))
            if not event.get("source"):
                event["source"] = str(event.get("source_type") or event.get("event_type") or "generic")
            if not event.get("subject"):
                event["subject"] = str(event.get("source", "System"))
            if not event.get("action"):
                event["action"] = str(event.get("event_type", "activity"))
            if not event.get("object"):
                event["object"] = "event"
            if not event.get("description"):
                event["description"] = _generate_plain_english_description(event)
            responses.append(EventResponse.model_validate(event))
        except Exception as exc:
            logger.debug(f"[events] Skipping event {event.get('_id')}: {exc}")
            continue

    return {
        "events": responses,
        "total": res["total"],
        "page": res["page"],
        "limit": res["limit"],
        "total_pages": res["total_pages"]
    }


@router.get("/cases/{case_id}/stats")
async def get_case_event_stats(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Retrieve exact uncapped event counts (total, anomalies, critical) for a case."""
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")
    return await EventRepository.count_case_stats(case_id, current_user.organization_id)
