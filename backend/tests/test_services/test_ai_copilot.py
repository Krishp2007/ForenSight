import sys
import os
import io
from fastapi.testclient import TestClient

# Force UTF-8 terminal encoding on Windows stdout/stderr to print emojis safely
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.app.main import app
from backend.app.worker.parser_tasks import process_evidence_task
from backend.app.worker.ml_tasks import run_anomaly_detection_task
from backend.app.worker.embedding_tasks import generate_event_embeddings_task

def test_ai_copilot_flow():
    print("==================================================")
    print("   FORENSIGHT AI COPILOT & VECTOR SEARCH TEST    ")
    print("==================================================")
    
    with TestClient(app) as client:
        # 1. Create Organization
        import uuid
        unique_suffix = uuid.uuid4().hex[:6]
        org_name = f"AI Lab {unique_suffix}"
        org_res = client.post("/api/v1/organizations/", json={"name": org_name})
        assert org_res.status_code == 201
        org_id = org_res.json()["id"]
        
        # 2. Register Investigator
        email = f"ai_{unique_suffix}@forensight.org"
        username = f"ai_analyst_{unique_suffix}"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "username": username,
            "organization_id": org_id,
            "password": "AIPassword123",
            "role": "investigator",
            "is_active": True
        })
        
        # 3. Login
        login_res = client.post("/api/v1/auth/login", data={"username": email, "password": "AIPassword123"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 4. Create Case
        case_res = client.post(
            "/api/v1/cases/", 
            json={"title": "AI Audit Case", "description": "Gemini AI Copilot and Vector Similarity Search Integration Test"}, 
            headers=headers
        )
        case_id = case_res.json()["id"]
        
        # 5. Build mock dataset with 6 events (to satisfy Isolation Forest minimum limit)
        csv_data = (
            "Timestamp,Event_Type,Subject,Action,Object,Severity\n"
            "2026-07-13 10:00:00,process_creation,explorer.exe,spawned,chrome.exe,info\n"
            "2026-07-13 10:05:00,process_creation,explorer.exe,spawned,slack.exe,info\n"
            "2026-07-13 10:10:00,process_creation,explorer.exe,spawned,vscode.exe,info\n"
            "2026-07-13 10:15:00,process_creation,explorer.exe,spawned,excel.exe,info\n"
            "2026-07-13 10:20:00,process_creation,explorer.exe,spawned,spotify.exe,info\n"
            "2026-07-18 03:00:00,process_creation,powershell.exe,spawned,malware_download_payload.ps1,critical\n"
        ).encode("utf-8")
        
        upload_res = client.post(
            f"/api/v1/cases/{case_id}/evidence",
            files={"file": ("raw_logs.csv", io.BytesIO(csv_data), "text/csv")},
            headers=headers
        )
        assert upload_res.status_code == 202
        evidence_id = upload_res.json()["id"]
        
        # 6. Parse events synchronously
        print("Parsing logs...")
        parser_result = process_evidence_task(evidence_id, org_id)
        assert parser_result["status"] == "completed"
        
        # 7. Run Anomaly detection model synchronously
        print("Running Outlier Anomaly Detection model...")
        ml_result = run_anomaly_detection_task(case_id, org_id)
        assert ml_result["status"] == "completed"
        
        # 8. Run Vector indexing task synchronously
        print("Generating Vector search FAISS index...")
        embed_result = generate_event_embeddings_task(case_id, org_id)
        assert embed_result["indexed"] is True
        print("[OK] Vector embedding indexing succeeded.")
        
        # 9. Query Semantic Search API
        print("\nTesting Semantic Similarity Search API...")
        search_res = client.get(f"/api/v1/cases/{case_id}/search?query=powershell script download", headers=headers)
        assert search_res.status_code == 200
        search_results = search_res.json()
        print(f"[OK] Fetched {len(search_results)} search results.")
        
        # Verify that powershell execution is returned as top search match
        top_match = search_results[0]
        print(f"  Top Match Subject: {top_match['subject']} | Object: {top_match['object']} | Distance: {top_match.get('distance'):.4f}")
        assert "powershell.exe" in top_match["subject"] or "powershell.exe" in top_match["object"] or "malware_download_payload.ps1" in top_match["object"]
        print("[OK] Semantic query matched the PowerShell threat context!")
        
        # 10. Query Gemini Copilot API
        print("\nTesting AI Copilot Endpoint...")
        copilot_res = client.post(
            f"/api/v1/cases/{case_id}/copilot",
            json={"question": "Summarize the critical anomalies and suggest next steps."},
            headers=headers
        )
        assert copilot_res.status_code == 200
        analysis_report = copilot_res.json()["analysis"]
        print(f"\nAI Analysis Report generated successfully (length: {len(analysis_report)} chars):")
        print("--------------------------------------------------")
        # Print first 10 lines of report
        print("\n".join(analysis_report.split("\n")[:15]))
        print("--------------------------------------------------")
        
        assert len(analysis_report) > 100
        assert "powershell.exe" in analysis_report or "malware_download_payload.ps1" in analysis_report
        print("[OK] AI Audit Report compiles critical threat factors successfully!")

    print("\n==================================================")
    print("   AI COPILOT & SEMANTIC FLOW CHECKS PASSED!     ")
    print("==================================================")

if __name__ == "__main__":
    test_ai_copilot_flow()
