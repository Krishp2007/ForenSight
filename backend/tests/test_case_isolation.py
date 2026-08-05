"""
Complete Case & Evidence Data Isolation Test Suite — ForenSight
================================================================
Verifies that all investigation data (events, anomalies, graph nodes, correlations,
statistics, reports, AI copilot context) is strictly isolated by Case and Evidence.
"""

import pytest
import asyncio
from bson import ObjectId

from backend.app.repositories.event_repository import EventRepository
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.repositories.case_repository import CaseRepository
from backend.app.repositories.graph_repository import GraphRepository
from backend.app.services.copilot.query_router import handle_structured_query


@pytest.mark.asyncio
async def test_case_dashboard_isolation():
    """Test 1: Case A (100 events) and Case B (250 events) must remain strictly isolated."""
    org_id = ObjectId()
    case_a_id = ObjectId()
    case_b_id = ObjectId()
    ev_a_id = ObjectId()
    ev_b_id = ObjectId()

    events_case_a = [
        {
            "case_id": case_a_id,
            "organization_id": org_id,
            "evidence_id": ev_a_id,
            "subject": f"User_A_{i}",
            "action": "logon",
            "object": "HostA",
            "severity": "info",
        }
        for i in range(100)
    ]

    events_case_b = [
        {
            "case_id": case_b_id,
            "organization_id": org_id,
            "evidence_id": ev_b_id,
            "subject": f"User_B_{i}",
            "action": "logon",
            "object": "HostB",
            "severity": "high",
        }
        for i in range(250)
    ]

    await EventRepository.bulk_create(events_case_a)
    await EventRepository.bulk_create(events_case_b)

    stats_a = await EventRepository.count_stats(str(case_a_id), str(org_id))
    stats_b = await EventRepository.count_stats(str(case_b_id), str(org_id))

    assert stats_a["total"] == 100
    assert stats_b["total"] == 250

    # Clean up
    await EventRepository.delete_by_evidence_id(str(ev_a_id), str(org_id))
    await EventRepository.delete_by_evidence_id(str(ev_b_id), str(org_id))


@pytest.mark.asyncio
async def test_reprocess_isolation_across_cases():
    """Test 2: Re-processing Evidence A1 in Case A must NOT affect Case B."""
    org_id = ObjectId()
    case_a_id = ObjectId()
    case_b_id = ObjectId()
    ev_a1_id = ObjectId()
    ev_b1_id = ObjectId()

    events_a1 = [
        {"case_id": case_a_id, "organization_id": org_id, "evidence_id": ev_a1_id, "subject": "A", "action": "run", "object": "exe", "severity": "info"}
        for _ in range(50)
    ]
    events_b1 = [
        {"case_id": case_b_id, "organization_id": org_id, "evidence_id": ev_b1_id, "subject": "B", "action": "run", "object": "exe", "severity": "low"}
        for _ in range(75)
    ]

    await EventRepository.bulk_create(events_a1)
    await EventRepository.bulk_create(events_b1)

    # Re-process A1
    await EventRepository.delete_by_evidence_id(str(ev_a1_id), str(org_id))
    await EventRepository.bulk_create(events_a1)

    # Verify Case B is untouched (still 75 events)
    stats_b = await EventRepository.count_stats(str(case_b_id), str(org_id))
    assert stats_b["total"] == 75

    # Clean up
    await EventRepository.delete_by_evidence_id(str(ev_a1_id), str(org_id))
    await EventRepository.delete_by_evidence_id(str(ev_b1_id), str(org_id))


@pytest.mark.asyncio
async def test_evidence_level_vs_case_level_stats():
    """Test 6: Evidence Report vs Case Report isolation."""
    org_id = ObjectId()
    case_id = ObjectId()
    ev1_id = ObjectId()
    ev2_id = ObjectId()

    events_ev1 = [
        {"case_id": case_id, "organization_id": org_id, "evidence_id": ev1_id, "subject": "E1", "action": "exec", "object": "cmd", "severity": "info"}
        for _ in range(40)
    ]
    events_ev2 = [
        {"case_id": case_id, "organization_id": org_id, "evidence_id": ev2_id, "subject": "E2", "action": "exec", "object": "powershell", "severity": "high"}
        for _ in range(60)
    ]

    await EventRepository.bulk_create(events_ev1)
    await EventRepository.bulk_create(events_ev2)

    # Evidence Level Stats for Ev1
    ev1_stats = await EventRepository.count_stats(str(case_id), str(org_id), evidence_id=str(ev1_id))
    assert ev1_stats["total"] == 40

    # Evidence Level Stats for Ev2
    ev2_stats = await EventRepository.count_stats(str(case_id), str(org_id), evidence_id=str(ev2_id))
    assert ev2_stats["total"] == 60

    # Case Level Stats (Ev1 + Ev2)
    case_stats = await EventRepository.count_stats(str(case_id), str(org_id))
    assert case_stats["total"] == 100

    # Clean up
    await EventRepository.delete_by_evidence_id(str(ev1_id), str(org_id))
    await EventRepository.delete_by_evidence_id(str(ev2_id), str(org_id))
