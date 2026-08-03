import sys
import os
import io
from fastapi.testclient import TestClient

# Force UTF-8 terminal encoding on Windows stdout/stderr to print emojis safely
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
from backend.app.worker.parser_tasks import process_evidence_task
from backend.app.worker.ml_tasks import run_anomaly_detection_task
from backend.app.worker.embedding_tasks import generate_event_embeddings_task

def test_report_compilation_flow():
    print("==================================================")
    print("   FORENSIGHT REPORT COMPILER INTEGRATION TEST   ")
    print("==================================================")
    
    with TestClient(app) as client:
        # 1. Create Organization
        import uuid
        unique_suffix = uuid.uuid4().hex[:6]
        org_name = f"Report Org {unique_suffix}"
        org_res = client.post("/api/v1/organizations/", json={"name": org_name})
        assert org_res.status_code == 201
        org_id = org_res.json()["id"]
        
        # 2. Register Investigator
        email = f"rep_{unique_suffix}@forensight.org"
        username = f"rep_analyst_{unique_suffix}"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "username": username,
            "organization_id": org_id,
            "password": "ReportPassword123",
            "role": "investigator",
            "is_active": True
        })
        
        # 3. Login
        login_res = client.post("/api/v1/auth/login", data={"username": email, "password": "ReportPassword123"})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 4. Create Case
        case_res = client.post(
            "/api/v1/cases/", 
            json={"title": "PDF Compilation Audit", "description": "Verifying Jinja templates and WeasyPrint compiler loops"}, 
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
        process_evidence_task(evidence_id, org_id)
        
        # 7. Run Anomaly detection model synchronously
        print("Running Outlier Anomaly Detection model...")
        run_anomaly_detection_task(case_id, org_id)
        
        # 8. Run Vector indexing task synchronously
        print("Generating Vector search FAISS index...")
        generate_event_embeddings_task(case_id, org_id)
        
        # 9. Test HTML Preview Endpoint
        print("\nTesting HTML Preview report endpoint...")
        html_res = client.get(f"/api/v1/cases/{case_id}/report/html", headers=headers)
        assert html_res.status_code == 200
        html_report = html_res.text
        print(f"[OK] Fetched HTML report successfully (length: {len(html_report)} chars)")
        
        assert "FORENSIGHT AI" in html_report
        assert "PDF Compilation Audit" in html_report
        assert "malware_download_payload.ps1" in html_report
        print("[OK] HTML preview includes case description, stats, and critical outlier flags.")
        
        # 10. Test PDF Endpoint (Handles whether Cairo dependencies are present or absent)
        print("\nTesting PDF download report endpoint...")
        pdf_res = client.get(f"/api/v1/cases/{case_id}/report/pdf", headers=headers)
        
        if pdf_res.status_code == 200:
            pdf_bytes = pdf_res.content
            print(f"[OK] PDF compiled and downloaded successfully! Size: {len(pdf_bytes)} bytes")
            assert pdf_bytes.startswith(b"%PDF")
            print("[OK] PDF signature matches binary standard %PDF header.")
        elif pdf_res.status_code == 424:
            print("[INFO] WeasyPrint missing Cairo system dependencies (Status 424). Fallback preview was suggested successfully:")
            print(f"  - Message: {pdf_res.json()['detail']}")
            assert "WeasyPrint system level libraries" in pdf_res.json()['detail']
        else:
            print(f"[FAIL] Unexpected response status code: {pdf_res.status_code}")
            assert False
            
    print("\n==================================================")
    print("   FORENSIGHT REPORT COMPILER INTEGRATION PASSED! ")
    print("==================================================")

if __name__ == "__main__":
    test_report_compilation_flow()
