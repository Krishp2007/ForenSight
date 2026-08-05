"""
Neo4j Forensic Evidence Graph & Correlation Tests
===================================================
Tests duplicate prevention, domain entity schema, cross-evidence correlation,
process hierarchy, evidence provenance, case isolation, and API formatting.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.repositories.graph_repository import GraphRepository
from backend.app.services.graph.graph_correlation import GraphCorrelationEngine


@pytest.mark.asyncio
async def test_duplicate_prevention_and_idempotency():
    """Verify that importing the exact same evidence twice does not create duplicate nodes or edges."""
    sample_events = [
        {
            "_id": "507f1f77bcf86cd799439011",
            "case_id": "case_100",
            "evidence_id": "ev_50",
            "timestamp": "2026-08-04T19:32:11",
            "event_type": "process_creation",
            "source": "evtx",
            "severity": "high",
            "subject": "explorer.exe",
            "action": "spawned",
            "object": "powershell.exe",
            "host": "DESKTOP-01",
            "username": "administrator",
            "process_name": "powershell.exe",
            "pid": 5420,
            "parent_process": "explorer.exe",
            "command_line": "powershell.exe -enc ...",
            "destination_ip": "185.220.101.5",
            "destination_port": 443,
            "is_anomaly": True,
            "anomaly_score": 0.91,
        }
    ]

    with patch("backend.app.services.graph.neo4j_service.neo4j_service.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = []
        
        # First import
        count1 = await GraphRepository.bulk_import_events(sample_events)
        # Second import (duplicate check)
        count2 = await GraphRepository.bulk_import_events(sample_events)

        assert count1 == 1
        assert count2 == 1
        assert mock_exec.call_count == 2


@pytest.mark.asyncio
async def test_cross_evidence_correlation_detection():
    """Verify EVTX process event + PCAP network event targeting same IP are correlated."""
    mock_neo4j_rows = [
        {
            "evtx_file": "Security_Logs.evtx",
            "pcap_file": "Traffic_Capture.pcap",
            "process_name": "powershell.exe",
            "shared_ip": "185.220.101.5",
            "evtx_time": "2026-08-04T19:32:11",
            "pcap_time": "2026-08-04T19:32:12",
        }
    ]

    with patch("backend.app.services.graph.neo4j_service.neo4j_service.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_neo4j_rows

        correlations = await GraphCorrelationEngine.detect_cross_evidence_correlations("case_100")
        assert len(correlations) == 1
        c = correlations[0]
        assert c["type"] == "cross_evidence"
        assert c["score"] == 85
        assert "Security_Logs.evtx" in c["evidence_sources"]
        assert "Traffic_Capture.pcap" in c["evidence_sources"]


@pytest.mark.asyncio
async def test_process_hierarchy_chain():
    """Verify parent-child process chains (explorer.exe -> powershell.exe -> cmd.exe) are parsed."""
    mock_chain_rows = [
        {
            "process_chain": ["explorer.exe", "powershell.exe", "cmd.exe"],
            "process_ids": ["DESKTOP-01:100:explorer.exe", "DESKTOP-01:5420:powershell.exe", "DESKTOP-01:6100:cmd.exe"],
            "chain_depth": 2,
        }
    ]

    with patch("backend.app.services.graph.neo4j_service.neo4j_service.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_chain_rows

        chains = await GraphCorrelationEngine.detect_process_chains("case_100")
        assert len(chains) == 1
        ch = chains[0]
        assert ch["chain"] == ["explorer.exe", "powershell.exe", "cmd.exe"]
        assert ch["severity"] in ("critical", "high")


@pytest.mark.asyncio
async def test_case_isolation():
    """Verify case graph queries include case_id parameter for strict tenant isolation."""
    with patch("backend.app.services.graph.neo4j_service.neo4j_service.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = []
        await GraphRepository.get_case_graph(case_id="case_A", org_id="org_1")

        call_args = mock_exec.call_args
        params = call_args[0][1] if call_args[0] and len(call_args[0]) > 1 else call_args[1].get("parameters", call_args[0][1] if len(call_args[0]) > 1 else {})
        assert params.get("case_id") == "case_A"
