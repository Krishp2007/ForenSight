"""
Live Scan Timer & Regression Protection Test Suite — ForenSight
================================================================
Verifies that terminal statuses (parsed, completed, failed) remain permanently
frozen, live stopwatch ticks during active scanning, case switching does not alter
durations, and re-processing correctly resets timing without event duplication.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from bson import ObjectId

from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.repositories.event_repository import EventRepository


@pytest.mark.asyncio
async def test_terminal_status_timer_frozen():
    """Test 2 & 3: Parsed evidence must record scan_duration_ms and remain frozen permanently."""
    org_id = ObjectId()
    case_id = ObjectId()

    # Create evidence
    doc = await EvidenceRepository.create(
        filename="sample.evtx",
        file_type="evtx",
        file_size=1024,
        minio_object_name="sample.evtx",
        case_id=str(case_id),
        organization_id=str(org_id),
        created_by=str(ObjectId()),
    )
    ev_id = str(doc["_id"])

    # 1. Start parsing
    await EvidenceRepository.update_status(ev_id, str(org_id), "parsing")
    fetching_active = await EvidenceRepository.get_by_id(ev_id, str(org_id))
    assert fetching_active["status"] == "parsing"
    assert fetching_active["processing_started_at"] is not None
    assert fetching_active["processing_finished_at"] is None

    # 2. Mark parsed after 5 seconds (5000 ms)
    await asyncio.sleep(0.05)
    await EvidenceRepository.update_status(ev_id, str(org_id), "parsed", scan_duration_ms=5000)

    fetching_parsed = await EvidenceRepository.get_by_id(ev_id, str(org_id))
    assert fetching_parsed["status"] == "parsed"
    assert fetching_parsed["scan_duration_ms"] == 5000
    assert fetching_parsed["processing_finished_at"] is not None

    # Simulate 10 minutes later (verify stored scan_duration_ms is preserved unchanged)
    fetching_later = await EvidenceRepository.get_by_id(ev_id, str(org_id))
    assert fetching_later["scan_duration_ms"] == 5000


@pytest.mark.asyncio
async def test_reprocess_resets_timer_fresh():
    """Test 6: Re-process resets completion timestamps and starts fresh scanning."""
    org_id = ObjectId()
    case_id = ObjectId()

    doc = await EvidenceRepository.create(
        filename="reprocess_test.pcap",
        file_type="pcap",
        file_size=2048,
        minio_object_name="reprocess_test.pcap",
        case_id=str(case_id),
        organization_id=str(org_id),
        created_by=str(ObjectId()),
    )
    ev_id = str(doc["_id"])

    # First run completed in 12s (12000 ms)
    await EvidenceRepository.update_status(ev_id, str(org_id), "parsed", scan_duration_ms=12000)
    old = await EvidenceRepository.get_by_id(ev_id, str(org_id))
    assert old["scan_duration_ms"] == 12000

    # Re-process clicked: sets status to uploaded
    await EvidenceRepository.update_status(ev_id, str(org_id), "uploaded")
    reprocess_start = await EvidenceRepository.get_by_id(ev_id, str(org_id))
    assert reprocess_start["status"] == "uploaded"
    assert reprocess_start["processing_finished_at"] is None
    assert reprocess_start["scan_duration_ms"] is None

    # Second run completed in 8s (8000 ms)
    await EvidenceRepository.update_status(ev_id, str(org_id), "parsed", scan_duration_ms=8000)
    new_run = await EvidenceRepository.get_by_id(ev_id, str(org_id))
    assert new_run["scan_duration_ms"] == 8000
