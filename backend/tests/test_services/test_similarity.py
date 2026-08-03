import sys
import os
import io
import uuid
import asyncio
from fastapi.testclient import TestClient

# Force UTF-8 terminal encoding on Windows stdout/stderr to print emojis safely
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.app.main import app
from backend.app.worker.parser_tasks import process_evidence_task
from backend.app.worker.embedding_tasks import generate_event_embeddings_task
from backend.app.services.intelligence.similarity_service import SimilarityService

def test_similarity_service_flow():
    print("==================================================")
    print("      FORENSIGHT CASE SIMILARITY SERVICE TEST     ")
    print("==================================================")
    
    with TestClient(app) as client:
        # 1. Create Organization
        unique_suffix = uuid.uuid4().hex[:6]
        org_name = f"Similarity Lab {unique_suffix}"
        org_res = client.post("/api/v1/organizations/", json={"name": org_name})
        assert org_res.status_code == 201
        org_id = org_res.json()["id"]
        
        # 2. Register Investigator
        email = f"sim_{unique_suffix}@forensight.org"
        username = f"sim_analyst_{unique_suffix}"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "username": username,
            "organization_id": org_id,
            "password": "SimPassword123",
            "role": "investigator",
            "is_active": True
        })
        
        # 3. Login
        login_res = client.post("/api/v1/auth/login", data={"username": email, "password": "SimPassword123"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 4. Create Case A: Suspicious PowerShell activity
        case_a_res = client.post("/api/v1/cases/", json={"title": "Case A (Malicious PS)", "description": "Analyzing suspicious powershell payload execution"}, headers=headers)
        case_a_id = case_a_res.json()["id"]
        
        # 5. Create Case B: Similar suspicious activity
        case_b_res = client.post("/api/v1/cases/", json={"title": "Case B (Suspicious CLI)", "description": "Analyzing network command shell activity"}, headers=headers)
        case_b_id = case_b_res.json()["id"]
        
        # 6. Create Case C: Benign activity
        case_c_res = client.post("/api/v1/cases/", json={"title": "Case C (Normal Usage)", "description": "Analyzing ordinary corporate workstation usage"}, headers=headers)
        case_c_id = case_c_res.json()["id"]
        
        # --- UPLOAD EVIDENCE ---
        # Evidence A
        csv_a = (
            "Timestamp,Event_Type,Subject,Action,Object,Severity\n"
            "2026-07-13 10:00:00,process_creation,cmd.exe,spawn,powershell.exe -enc ZABvAHcAbgBsAG8AYQBk,critical\n"
            "2026-07-13 10:05:00,network_connection,powershell.exe,connect,185.220.101.45:4444,high\n"
            "2026-07-13 10:10:00,file_modification,powershell.exe,create,C:\\temp\\payload.exe,high\n"
        ).encode("utf-8")
        
        # Evidence B (Highly aligned process & network shell patterns)
        csv_b = (
            "Timestamp,Event_Type,Subject,Action,Object,Severity\n"
            "2026-07-13 10:02:00,process_creation,cmd.exe,spawn,powershell.exe -nop -executionpolicy bypass,critical\n"
            "2026-07-13 10:06:00,network_connection,powershell.exe,connect,103.45.67.89:8080,high\n"
            "2026-07-13 10:12:00,process_creation,powershell.exe,spawn,whoami.exe,medium\n"
        ).encode("utf-8")
        
        # Evidence C (Completely distinct benign workstation activities)
        csv_c = (
            "Timestamp,Event_Type,Subject,Action,Object,Severity\n"
            "2026-07-13 09:00:00,process_creation,explorer.exe,spawn,slack.exe,info\n"
            "2026-07-13 09:15:00,process_creation,slack.exe,read,harmless_config.json,info\n"
            "2026-07-13 09:30:00,process_creation,explorer.exe,spawn,chrome.exe,info\n"
        ).encode("utf-8")
        
        # Upload & Parse A
        up_a = client.post(f"/api/v1/cases/{case_a_id}/evidence", files={"file": ("logs_a.csv", io.BytesIO(csv_a), "text/csv")}, headers=headers)
        assert up_a.status_code == 202
        process_evidence_task(up_a.json()["id"], org_id)
        generate_event_embeddings_task(case_a_id, org_id)
        
        # Upload & Parse B
        up_b = client.post(f"/api/v1/cases/{case_b_id}/evidence", files={"file": ("logs_b.csv", io.BytesIO(csv_b), "text/csv")}, headers=headers)
        assert up_b.status_code == 202
        process_evidence_task(up_b.json()["id"], org_id)
        generate_event_embeddings_task(case_b_id, org_id)
        
        # Upload & Parse C
        up_c = client.post(f"/api/v1/cases/{case_c_id}/evidence", files={"file": ("logs_c.csv", io.BytesIO(csv_c), "text/csv")}, headers=headers)
        assert up_c.status_code == 202
        process_evidence_task(up_c.json()["id"], org_id)
        generate_event_embeddings_task(case_c_id, org_id)
        
        # Test Case Comparison through SimilarityService
        sim_ab = asyncio.run(SimilarityService.calculate_case_similarity(case_a_id, case_b_id, org_id))
        sim_ac = asyncio.run(SimilarityService.calculate_case_similarity(case_a_id, case_c_id, org_id))
        
        print(f"\nSimilarity Metrics Computed:")
        print(f"  - Case A (Malishing PS) <-> Case B (Suspicious CLI): {sim_ab:.4f}")
        print(f"  - Case A (Malishing PS) <-> Case C (Normal Usage) : {sim_ac:.4f}")
        
        # Ensure Case A holds significantly stronger semantic similarity with Case B than Case C
        assert sim_ab > sim_ac, "Case A should be semantically closer to Case B than Case C"
        print("  ✅ Cosine similarity ranking holds true!")
        
        # Test API Endpoint mapping
        similar_res = client.get(f"/api/v1/cases/{case_a_id}/similar-cases", headers=headers)
        assert similar_res.status_code == 200
        similar_cases = similar_res.json()
        
        print(f"\nSimilar Cases returned by API for Case A:")
        for sc in similar_cases:
            print(f"  - Case ID: {sc['case_id']} | Title: {sc['title']} | Score: {sc['similarity_score']:.4f}")
            
        assert len(similar_cases) > 0
        assert similar_cases[0]["case_id"] == case_b_id, "The highest similarity case should be Case B"
        print("  ✅ API /similar-cases successfully matched threat profiles!")

    print("\n==================================================")
    print("     CASE SIMILARITY INTEGRATION TEST PASSED!     ")
    print("==================================================")

if __name__ == "__main__":
    test_similarity_service_flow()
