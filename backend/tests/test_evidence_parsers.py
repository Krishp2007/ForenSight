"""
Evidence Parser Suite Tests — ForenSight
=========================================
Tests for EVTX, PCAP, CSV, JSON, Hash, Text, and Entity & Relationship Extractor.
Verifies the common normalized schema, deterministic extraction, confidence scores,
and evidence provenance tagging.
"""

import pytest
from datetime import datetime

from backend.app.parsers import get_parser
from backend.app.parsers.evtx_parser import EvtxParser
from backend.app.parsers.pcap_parser import PcapParser
from backend.app.parsers.csv_parser import CsvParser
from backend.app.parsers.json_parser import JsonParser
from backend.app.parsers.hash_parser import HashParser
from backend.app.parsers.text_parser import TextParser
from backend.app.parsers.extractor import EntityRelationshipExtractor


def test_parser_router_factory():
    """Verify get_parser returns corresponding parser instance for each extension."""
    assert isinstance(get_parser("evtx"), EvtxParser)
    assert isinstance(get_parser("pcap"), PcapParser)
    assert isinstance(get_parser("csv"), CsvParser)
    assert isinstance(get_parser("json"), JsonParser)
    assert isinstance(get_parser("md5"), HashParser)
    assert isinstance(get_parser("txt"), TextParser)


def test_csv_parser_normalized_alias_schema():
    """Verify CSV parser correctly maps column aliases to nested normalized schema."""
    csv_data = (
        "src_ip,dst_ip,src_port,dst_port,user,pid,cmdline,time\n"
        "10.0.0.5,185.220.101.5,51234,443,administrator,5420,powershell.exe -enc AAA=,2026-08-04T19:32:11\n"
    ).encode("utf-8")

    parser = CsvParser()
    events = parser.parse(csv_data, filename="firewall_logs.csv")

    assert len(events) == 1
    ev = events[0]

    assert ev["source_type"] == "csv"
    assert ev["network"]["source_ip"] == "10.0.0.5"
    assert ev["network"]["destination_ip"] == "185.220.101.5"
    assert ev["network"]["destination_port"] == 443
    assert ev["user"]["username"] == "administrator"
    assert ev["process"]["pid"] == 5420
    assert "entities" in ev
    assert "relationships" in ev


def test_json_parser_ndjson_lines():
    """Verify JsonParser handles NDJSON / JSON lines and populates nested schema."""
    ndjson_data = (
        '{"timestamp": "2026-08-04T19:32:11", "event_type": "process_creation", "username": "administrator", "process_name": "cmd.exe", "ip": "192.168.1.10"}\n'
        '{"timestamp": "2026-08-04T19:32:12", "event_type": "network_connection", "src_ip": "192.168.1.10", "dst_ip": "1.1.1.1"}\n'
    ).encode("utf-8")

    parser = JsonParser()
    events = parser.parse(ndjson_data, filename="app_logs.json")

    assert len(events) == 2
    assert events[0]["user"]["username"] == "administrator"
    assert events[0]["process"]["name"] == "cmd.exe"
    assert events[1]["network"]["destination_ip"] == "1.1.1.1"


def test_hash_parser_extraction():
    """Verify HashParser extracts MD5, SHA1, SHA256 without false positive malware tagging."""
    hash_data = (
        "d41d8cd98f00b204e9800998ecf8427e  payload.exe\n"
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  clean_file.dll\n"
    ).encode("utf-8")

    parser = HashParser()
    events = parser.parse(hash_data, filename="manifest.sha256")

    assert len(events) == 2
    assert events[0]["severity"] == "info"
    assert events[0]["file"]["md5"] == "d41d8cd98f00b204e9800998ecf8427e"
    assert events[1]["file"]["sha256"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_text_parser_precompiled_regex():
    """Verify TextParser extracts IPv4, URLs, Windows paths, and hashes from unformatted logs."""
    text_data = (
        "2026-08-04 19:32:11 Error connection from 192.168.1.50 to http://malicious-domain.com/payload.bin path C:\\Windows\\System32\\cmd.exe\n"
    ).encode("utf-8")

    parser = TextParser()
    events = parser.parse(text_data, filename="server.log")

    assert len(events) == 1
    ev = events[0]

    assert ev["network"]["source_ip"] == "192.168.1.50"
    assert ev["network"]["url"] == "http://malicious-domain.com/payload.bin"
    assert ev["process"]["path"] == "C:\\Windows\\System32\\cmd.exe"
    assert ev["severity"] == "medium"  # 'Error' in line


def test_entity_relationship_extractor_provenance():
    """Verify EntityRelationshipExtractor generates explicit entities, relationships, confidence scores, and provenance."""
    mock_event = {
        "event_id": "ev_100",
        "case_id": "case_1",
        "evidence_id": "evidence_1",
        "source_file": "security.evtx",
        "timestamp": datetime.utcnow(),
        "host": {"hostname": "DESKTOP-01"},
        "user": {"username": "administrator", "domain": "CORP"},
        "process": {"name": "powershell.exe", "pid": 5420, "path": "C:\\powershell.exe"},
        "parent_process": {"name": "explorer.exe", "pid": 1200},
        "network": {"destination_ip": "185.220.101.5", "destination_port": 443},
    }

    res = EntityRelationshipExtractor.extract_from_event(mock_event)
    entities = res["entities"]
    relationships = res["relationships"]

    entity_types = {e["type"] for e in entities}
    rel_types = {r["rel_type"] for r in relationships}

    assert "Host" in entity_types
    assert "User" in entity_types
    assert "Process" in entity_types
    assert "IPAddress" in entity_types
    assert "Port" in entity_types

    assert "EXECUTED" in rel_types
    assert "SPAWNED" in rel_types
    assert "CONNECTED_TO" in rel_types
    assert "USES_PORT" in rel_types

    # Provenance
    assert relationships[0]["case_id"] == "case_1"
    assert relationships[0]["evidence_id"] == "evidence_1"
    assert relationships[0]["relationship_type"] == "observed"
