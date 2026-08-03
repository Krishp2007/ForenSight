import sys
import os
import io
from fastapi.testclient import TestClient

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.app.main import app
from backend.app.worker.parser_tasks import process_evidence_task
from backend.app.db.mongodb import db_client, connect_to_mongo
from backend.app.repositories.event_repository import EventRepository
from backend.app.repositories.evidence_repository import EvidenceRepository

async def verify_events_stored(case_id: str, org_id: str, evidence_id: str):
    """Async database checks to verify background parsing succeeded."""
    # Automatically handled by lazy-scoped connection loader
    pass
        
    # 1. Check evidence status in database
    evidence = await EvidenceRepository.get_by_id(evidence_id, org_id)
    assert evidence is not None
    print(f"Evidence status in DB: {evidence['status']}")
    assert evidence["status"] == "parsed"
    
    # 2. Check events count in MongoDB
    events = await EventRepository.list_by_case(case_id, org_id)
    print(f"Parsed events found in DB: {len(events)}")
    assert len(events) > 0
    
    # Print the first event to show standard format
    first_event = events[0]
    print(f"Sample parsed CFM Event:")
    print(f"  - Timestamp: {first_event['timestamp']}")
    print(f"  - Type: {first_event['event_type']}")
    print(f"  - Subject: {first_event['subject']}")
    print(f"  - Action: {first_event['action']}")
    print(f"  - Object: {first_event['object']}")
    print(f"  - Severity: {first_event['severity']}")
    
def test_full_pipeline():
    print("==================================================")
    print("   FORENSIGHT INGESTION & PIPELINE TEST          ")
    print("==================================================")
    
    with TestClient(app) as client:
        # 1. Create Organization with unique name
        import uuid
        unique_suffix = uuid.uuid4().hex[:6]
        org_name = f"Pipeline Lab {unique_suffix}"
        org_res = client.post("/api/v1/organizations/", json={"name": org_name})
        assert org_res.status_code == 201
        org_id = org_res.json()["id"]
        
        # 2. Register Investigator
        email = f"pipeline_{unique_suffix}@forensight.org"
        username = f"pipeline_analyst_{unique_suffix}"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "username": username,
            "organization_id": org_id,
            "password": "PipelinePassword123",
            "role": "investigator",
            "is_active": True
        })
        
        # 3. Login
        login_res = client.post("/api/v1/auth/login", data={"username": email, "password": "PipelinePassword123"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 4. Create Case
        case_res = client.post("/api/v1/cases/", json={"title": "Pipeline Test Case", "description": "Celery Pipeline Test"}, headers=headers)
        case_id = case_res.json()["id"]
        
        # 5. Upload a mock CSV Timeline File
        csv_data = (
            "Timestamp,Event_Type,Subject,Action,Object,Severity\n"
            "2026-07-13 22:00:00,process_creation,cmd.exe,spawned,powershell.exe -enc XYZ,high\n"
            "2026-07-13 22:05:00,network_connection,10.0.0.5,connected_to,192.168.1.10:4444,medium\n"
        ).encode("utf-8")
        
        upload_res = client.post(
            f"/api/v1/cases/{case_id}/evidence",
            files={"file": ("timeline.csv", io.BytesIO(csv_data), "text/csv")},
            headers=headers
        )
        assert upload_res.status_code == 202
        evidence_data = upload_res.json()
        evidence_id = evidence_data["id"]
        
        # Note: Status returned is "queued" because ProcessingPipeline queued the task
        assert evidence_data["status"] == "queued"
        print(f"[OK] File uploaded and queued successfully. Evidence ID: {evidence_id}")
        
        # 6. Execute parser task synchronously (simulates background worker processing)
        print("\nExecuting processing task synchronously...")
        result = process_evidence_task(evidence_id, org_id)
        assert result["status"] == "completed"
        print("[OK] Task finished executing.")
        
        # 7. Verify status and CFM events in MongoDB
        import asyncio
        asyncio.run(verify_events_stored(case_id, org_id, evidence_id))
        
    print("\n==================================================")
    print("   PIPELINE AND DATABASE INTEGRATION PASSED!      ")
    print("==================================================")

if __name__ == "__main__":
    test_full_pipeline()
