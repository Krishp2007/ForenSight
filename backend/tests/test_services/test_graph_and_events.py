import sys
import os
import io
from fastapi.testclient import TestClient

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.app.main import app
from backend.app.worker.parser_tasks import process_evidence_task

def test_graph_and_events_flow():
    print("==================================================")
    print("   FORENSIGHT GRAPH & EVENTS INTEGRATION TEST    ")
    print("==================================================")
    
    with TestClient(app) as client:
        # 1. Create Organization
        import uuid
        unique_suffix = uuid.uuid4().hex[:6]
        org_name = f"Graph Lab {unique_suffix}"
        org_res = client.post("/api/v1/organizations/", json={"name": org_name})
        assert org_res.status_code == 201
        org_id = org_res.json()["id"]
        
        # 2. Register Investigator
        email = f"graph_{unique_suffix}@forensight.org"
        username = f"graph_analyst_{unique_suffix}"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "username": username,
            "organization_id": org_id,
            "password": "GraphPassword123",
            "role": "investigator",
            "is_active": True
        })
        
        # 3. Login
        login_res = client.post("/api/v1/auth/login", data={"username": email, "password": "GraphPassword123"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 4. Create Case
        case_res = client.post("/api/v1/cases/", json={"title": "Graph Test Case", "description": "Neo4j Graph Integration Test"}, headers=headers)
        case_id = case_res.json()["id"]
        
        # 5. Upload a mock CSV Timeline File containing standard attack events
        csv_data = (
            "Timestamp,Event_Type,Subject,Action,Object,Severity\n"
            "2026-07-13 23:00:00,process_creation,cmd.exe,spawned,powershell.exe,high\n"
            "2026-07-13 23:01:00,file_modification,powershell.exe,wrote,ransomware.exe,critical\n"
            "2026-07-13 23:02:00,network_connection,ransomware.exe,connected_to,8.8.8.8:443,medium\n"
        ).encode("utf-8")
        
        upload_res = client.post(
            f"/api/v1/cases/{case_id}/evidence",
            files={"file": ("incident.csv", io.BytesIO(csv_data), "text/csv")},
            headers=headers
        )
        assert upload_res.status_code == 202
        evidence_id = upload_res.json()["id"]
        
        # 6. Execute parser task synchronously to insert in MongoDB & Neo4j
        print("Processing task synchronously...")
        result = process_evidence_task(evidence_id, org_id)
        assert result["status"] == "completed"
        print("[OK] Background task completed processing.")
        
        # 7. Query Events timeline API with filters
        print("\nQuerying Events timeline API...")
        events_res = client.get(f"/api/v1/cases/{case_id}/events", headers=headers)
        assert events_res.status_code == 200
        events = events_res.json()
        print(f"[OK] Fetched {len(events)} events.")
        assert len(events) == 3
        
        # Check severity filter
        high_events_res = client.get(f"/api/v1/cases/{case_id}/events?severity=high", headers=headers)
        assert high_events_res.status_code == 200
        high_events = high_events_res.json()
        print(f"[OK] Fetched {len(high_events)} high severity events.")
        assert len(high_events) == 1
        assert high_events[0]["subject"] == "cmd.exe"
        
        # 8. Query Neo4j Graph API
        print("\nQuerying Neo4j Graph visualization API...")
        graph_res = client.get(f"/api/v1/cases/{case_id}/graph", headers=headers)
        assert graph_res.status_code == 200
        graph_data = graph_res.json()
        
        print(f"[OK] Graph loaded successfully:")
        print(f"  - Nodes count: {len(graph_data['nodes'])}")
        print(f"  - Edges count: {len(graph_data['edges'])}")
        
        # Check node type categorization
        nodes = graph_data["nodes"]
        node_map = {n["id"]: n["type"] for n in nodes}
        print("  Node Types Inferred:")
        for node_id, node_type in node_map.items():
            print(f"    * {node_id}: {node_type}")
            
        assert node_map["cmd.exe"] == "Process"
        assert node_map["powershell.exe"] == "Process"
        assert node_map["ransomware.exe"] == "Process"
        assert node_map["8.8.8.8:443"] == "NetworkAddress"
        
        # 9. Clear Case Graph API
        print("\nClearing Case Graph nodes...")
        clear_res = client.delete(f"/api/v1/cases/{case_id}/graph", headers=headers)
        assert clear_res.status_code == 204
        
        # Re-fetch graph to assert it's empty
        re_graph_res = client.get(f"/api/v1/cases/{case_id}/graph", headers=headers)
        assert re_graph_res.status_code == 200
        re_graph_data = re_graph_res.json()
        assert len(re_graph_data["nodes"]) == 0
        assert len(re_graph_data["edges"]) == 0
        print("[OK] Case graph cleared successfully from Neo4j.")

    print("\n==================================================")
    print("   GRAPH & EVENTS INTEGRATION CHECKS PASSED!     ")
    print("==================================================")

if __name__ == "__main__":
    test_graph_and_events_flow()
