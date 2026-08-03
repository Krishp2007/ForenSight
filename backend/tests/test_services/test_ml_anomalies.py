import sys
import os
import io
from fastapi.testclient import TestClient

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.app.main import app
from backend.app.worker.parser_tasks import process_evidence_task
from backend.app.worker.ml_tasks import run_anomaly_detection_task
from backend.app.repositories.event_repository import EventRepository
from backend.app.repositories.graph_repository import GraphRepository

def test_ml_anomaly_flow():
    print("==================================================")
    print("   FORENSIGHT ML ANOMALY DETECTION TEST         ")
    print("==================================================")
    
    with TestClient(app) as client:
        # 1. Create Organization
        import uuid
        unique_suffix = uuid.uuid4().hex[:6]
        org_name = f"ML Lab {unique_suffix}"
        org_res = client.post("/api/v1/organizations/", json={"name": org_name})
        assert org_res.status_code == 201
        org_id = org_res.json()["id"]
        
        # 2. Register Investigator
        email = f"ml_{unique_suffix}@forensight.org"
        username = f"ml_analyst_{unique_suffix}"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "username": username,
            "organization_id": org_id,
            "password": "MLPassword123",
            "role": "investigator",
            "is_active": True
        })
        
        # 3. Login
        login_res = client.post("/api/v1/auth/login", data={"username": email, "password": "MLPassword123"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 4. Create Case
        case_res = client.post("/api/v1/cases/", json={"title": "ML Case", "description": "Isolation Forest Outlier Detection Test"}, headers=headers)
        case_id = case_res.json()["id"]
        
        # 5. Build mock dataset with 20 normal logs (weekday daytime, common process)
        # and 1 obvious outlier (Saturday 3 AM, rare process, critical severity)
        csv_rows = ["Timestamp,Event_Type,Subject,Action,Object,Severity"]
        
        # 20 normal events
        for i in range(20):
            # Normal weekday hours (10 AM to 4 PM)
            csv_rows.append(f"2026-07-13 {10 + (i%6)}:00:00,process_creation,explorer.exe,spawned,chrome.exe,info")
            
        # 1 clear outlier event (Saturday 3:15 AM, rare backup deletion, critical severity)
        csv_rows.append("2026-07-18 03:15:00,process_creation,powershell.exe,spawned,vssadmin.exe delete shadows /all,critical")
        
        csv_data = "\n".join(csv_rows).encode("utf-8")
        
        upload_res = client.post(
            f"/api/v1/cases/{case_id}/evidence",
            files={"file": ("raw_logs.csv", io.BytesIO(csv_data), "text/csv")},
            headers=headers
        )
        assert upload_res.status_code == 202
        evidence_id = upload_res.json()["id"]
        
        # 6. Run parser task to load events into MongoDB & Neo4j
        print("Parsing logs...")
        parser_result = process_evidence_task(evidence_id, org_id)
        assert parser_result["status"] == "completed"
        
        # 7. Manually invoke ML task synchronously to calculate scores
        print("Running ML Anomaly Detection model...")
        ml_result = run_anomaly_detection_task(case_id, org_id)
        assert ml_result["status"] == "completed"
        print(f"[OK] Outlier search finished. Total processed: {ml_result['total_processed']} | Flagged: {ml_result['anomalies_detected']}")
        
        # 8. Query Events timeline and verify that outlier was correctly flagged
        events_res = client.get(f"/api/v1/cases/{case_id}/events", headers=headers)
        events = events_res.json()
        
        outliers = [e for e in events if e.get("is_anomaly")]
        print(f"\nFound {len(outliers)} events flagged as outliers:")
        for o in outliers:
            print(f"  - Subject: {o['subject']}")
            print(f"  - Object: {o['object']}")
            print(f"  - Score: {o['anomaly_score']:.4f}")
            print(f"  - Timestamp: {o['timestamp']}")
            
        # Ensure our outlier (vssadmin.exe) was indeed caught
        outlier_subjects = [o["object"] for o in outliers]
        assert any("vssadmin.exe" in obj for obj in outlier_subjects)
        print("[OK] Outlier vssadmin.exe successfully isolated!")
        
        # 9. Verify Neo4j Case Graph contains anomaly annotations
        graph_res = client.get(f"/api/v1/cases/{case_id}/graph", headers=headers)
        graph_data = graph_res.json()
        
        edges = graph_data["edges"]
        anomaly_edges = [e for e in edges if e.get("is_anomaly")]
        print(f"\nNeo4j graph edges flagged as anomalies: {len(anomaly_edges)}")
        for ae in anomaly_edges:
            print(f"  - {ae['source']} -> [{ae['action']}] -> {ae['target']} (Score: {ae['anomaly_score']:.4f})")
            
        assert len(anomaly_edges) > 0
        print("[OK] Neo4j relationship markers updated successfully!")
        
    print("\n==================================================")
    print("   ML OUTLIER DETECTION INTEGRATION PASSED!      ")
    print("==================================================")

if __name__ == "__main__":
    test_ml_anomaly_flow()
