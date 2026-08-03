import sys
import os
import io
from datetime import datetime

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
from backend.app.worker.parser_tasks import process_evidence_task
from backend.app.worker.ml_tasks import run_anomaly_detection_task
from backend.app.worker.embedding_tasks import generate_event_embeddings_task

def generate_demo_files():
    print("==================================================")
    print("      FORENSIGHT COMPLETE PIPELINE INTEGRATION    ")
    print("==================================================")
    
    from fastapi.testclient import TestClient
    
    # Starting TestClient automatically handles lifespan (starts mongo/neo4j/redis connections)
    with TestClient(app) as client:
        import uuid
        unique_suffix = uuid.uuid4().hex[:6]
        org_name = f"Demo Org {unique_suffix}"
        
        # 1. Create Organization via REST API
        org_res = client.post("/api/v1/organizations/", json={"name": org_name})
        assert org_res.status_code == 201
        org_id = org_res.json()["id"]
        
        # 2. Create investigator credentials and log in
        username = f"analyst_{unique_suffix}"
        email = f"{username}@forensight.org"
        register_res = client.post("/api/v1/auth/register", json={
            "email": email,
            "username": username,
            "organization_id": org_id,
            "password": "DemoPassword123",
            "role": "investigator",
            "is_active": True
        })
        assert register_res.status_code == 201
        
        login_res = client.post("/api/v1/auth/login", data={"username": email, "password": "DemoPassword123"})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create Case via REST API
        case_res = client.post(
            "/api/v1/cases/", 
            json={
                "title": "ForenSight End-to-End Audit", 
                "description": "This is a full pipeline verification. It integrates log parsing, Isolation Forest anomaly mapping, Neo4j graph relational indexing, FAISS semantic vector search, and HTML/PDF report compilation."
            }, 
            headers=headers
        )
        assert case_res.status_code == 201
        case_id = case_res.json()["id"]
        
        # 4. Mock csv data containing a normal timeline alongside critical anomaly trails
        csv_data = (
            "Timestamp,Event_Type,Subject,Action,Object,Severity\n"
            "2026-07-13 10:00:00,process_creation,explorer.exe,spawned,chrome.exe,info\n"
            "2026-07-13 10:05:00,process_creation,explorer.exe,spawned,slack.exe,info\n"
            "2026-07-13 10:10:00,process_creation,explorer.exe,spawned,vscode.exe,info\n"
            "2026-07-13 10:15:00,process_creation,explorer.exe,spawned,excel.exe,info\n"
            "2026-07-13 10:20:00,process_creation,explorer.exe,spawned,spotify.exe,info\n"
            "2026-07-18 03:00:00,process_creation,powershell.exe,spawned,malware_download_payload.ps1,critical\n"
            "2026-07-18 03:05:00,network_connection,powershell.exe,connected_to,8.8.8.8:443,critical\n"
            "2026-07-18 03:10:00,registry_modification,powershell.exe,modified,HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run,critical\n"
        )
        
        # 5. Upload evidence file
        print("\n[1/5] Uploading evidence log file...")
        upload_res = client.post(
            f"/api/v1/cases/{case_id}/evidence",
            files={"file": ("incident_logs.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
            headers=headers
        )
        assert upload_res.status_code == 202
        ev_id = upload_res.json()["id"]
        print(f"-> Evidence uploaded successfully. ID: {ev_id}")
        
        # 6. Execute core pipelines
        print("\n[2/5] Parsing CSV logs and generating event timeline...")
        process_evidence_task(ev_id, org_id)
        
        print("\n[3/5] Performing Machine Learning Anomaly Detection (Isolation Forest)...")
        run_anomaly_detection_task(case_id, org_id)
        
        print("\n[4/5] Building FAISS Vector embeddings index...")
        generate_event_embeddings_task(case_id, org_id)
        
        # 7. Generate and save html report
        print("\n[5/5] Compiling case incident report...")
        html_res = client.get(f"/api/v1/cases/{case_id}/report/html", headers=headers)
        assert html_res.status_code == 200
        html_content = html_res.text
        
        html_output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_demo.html")
        with open(html_output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"-> HTML preview report generated successfully! Saved to: {html_output_path}")
        
        # 8. Generate and save PDF report
        pdf_output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_demo.pdf")
        pdf_res = client.get(f"/api/v1/cases/{case_id}/report/pdf", headers=headers)
        
        if pdf_res.status_code == 200:
            with open(pdf_output_path, "wb") as f:
                f.write(pdf_res.content)
            print(f"-> Binary PDF report compiled successfully! Saved to: {pdf_output_path}")
        else:
            print("\n[NOTE] WeasyPrint system level libraries (Pango/Cairo) are not configured on this Windows host.")
            print("You can easily download the print-ready PDF:")
            print(f"1. Double click to open: {html_output_path} in your browser.")
            print("2. Press Ctrl+P (Print) -> Select 'Save as PDF' -> Click Save.")
            
    print("\nComplete execution done!")

if __name__ == "__main__":
    generate_demo_files()
