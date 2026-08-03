import sys
import os
import sqlite3
import tempfile
from datetime import datetime

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.app.parsers import get_parser, EvtxParser, BrowserParser, CsvParser, JsonParser

def test_evtx_fallback():
    print("Testing EVTX Parser fallback...")
    parser = get_parser("evtx")
    assert isinstance(parser, EvtxParser)
    
    # Test fallback handling of plain text dummy file
    events = parser.parse(b"dummy evtx data", filename="security.evtx")
    assert len(events) == 1
    assert events[0]["object"] == "security.evtx"
    assert events[0]["event_type"] == "generic"
    print("[OK] EVTX Parser fallback verification passed!")

def test_browser_sqlite_parser():
    print("\nTesting Browser SQLite Parser (Chrome table)...")
    parser = get_parser("browser")
    assert isinstance(parser, BrowserParser)
    
    # 1. Create a temporary SQLite database mimicking Chrome history urls table
    with tempfile.NamedTemporaryFile(delete=False) as tmp_db:
        db_path = tmp_db.name
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create Chrome urls table structure
        cursor.execute("""
            CREATE TABLE urls (
                id INTEGER PRIMARY KEY,
                url TEXT,
                title TEXT,
                visit_count INTEGER,
                last_visit_time INTEGER
            );
        """)
        
        # Insert test records (Chrome last_visit_time is microseconds since 1601-01-01)
        # For simplicity, we write 13253760000000000 (roughly Year 2021)
        cursor.execute("""
            INSERT INTO urls (url, title, visit_count, last_visit_time)
            VALUES ('https://torproject.org', 'Tor Project', 2, 13253760000000000),
                   ('https://malicious.com/payload.exe', 'Payload', 1, 13253761000000000);
        """)
        conn.commit()
        conn.close()
        
        # Read file bytes
        with open(db_path, "rb") as f:
            db_bytes = f.read()
            
        # Parse bytes
        events = parser.parse(db_bytes, filename="ChromeHistory")
        assert len(events) == 2
        
        # The tor domain should trigger EventSeverity.HIGH (T1090.003)
        assert any(e["severity"] == "high" for e in events)
        # The payload.exe download should trigger EventSeverity.MEDIUM (T1105)
        assert any(e["severity"] == "medium" for e in events)
        
        print(f"[OK] Browser Parser successfully extracted {len(events)} history events from Chrome SQLite bytes!")
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)

def test_csv_parser():
    print("\nTesting CSV Parser...")
    parser = get_parser("csv")
    assert isinstance(parser, CsvParser)
    
    csv_content = (
        "Timestamp,Event_Type,Subject,Action,Object,Severity\n"
        "2026-07-10 12:00:00,process_creation,cmd.exe,spawned,powershell.exe,medium\n"
        "2026-07-10 12:05:00,network_connection,192.168.1.100,connected_to,8.8.8.8,info\n"
    ).encode("utf-8")
    
    events = parser.parse(csv_content, filename="timeline.csv")
    assert len(events) == 2
    assert events[0]["event_type"] == "process_creation"
    assert events[0]["subject"] == "cmd.exe"
    assert events[0]["action"] == "spawned"
    assert events[0]["object"] == "powershell.exe"
    assert events[0]["severity"] == "medium"
    
    assert events[1]["event_type"] == "network_connection"
    assert events[1]["subject"] == "192.168.1.100"
    print("[OK] CSV Parser successfully aligned and normalized CSV rows!")

def test_json_parser():
    print("\nTesting JSON Parser...")
    parser = get_parser("json")
    assert isinstance(parser, JsonParser)
    
    json_content = """[
        {
            "timestamp": "2026-07-10 12:10:00",
            "event_type": "file_modification",
            "subject": "explorer.exe",
            "action": "deleted",
            "object": "C:\\\\tmp\\\\evidence.log",
            "severity": "low"
        }
    ]""".encode("utf-8")
    
    events = parser.parse(json_content, filename="report.json")
    assert len(events) == 1
    assert events[0]["event_type"] == "file_modification"
    assert events[0]["subject"] == "explorer.exe"
    assert events[0]["action"] == "deleted"
    assert events[0]["object"] == "C:\\tmp\\evidence.log"
    assert events[0]["severity"] == "low"
    print("[OK] JSON Parser successfully mapped list arrays to CFM events!")

if __name__ == "__main__":
    print("Starting local forensic parsers unit tests...")
    try:
        test_evtx_fallback()
        test_browser_sqlite_parser()
        test_csv_parser()
        test_json_parser()
        print("\nALL PARSER INTEGRATION CHECKS PASSED PERFECTLY!")
    except Exception as e:
        print(f"\nParser tests failed: {e}")
