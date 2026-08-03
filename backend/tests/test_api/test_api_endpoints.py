import sys
import os
import io
from fastapi.testclient import TestClient

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.app.main import app

def test_root_endpoint(client):
    print("Testing Root status endpoint...")
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("[OK] Root endpoint verified successfully!")

def test_organization_and_auth_flow(client):
    print("\nTesting Organization and Auth REST Flows...")
    
    # 1. Create unique organization
    org_name = f"Test Lab - {os.urandom(4).hex()}"
    org_response = client.post("/api/v1/organizations/", json={"name": org_name})
    assert org_response.status_code == 201
    org_data = org_response.json()
    org_id = org_data["id"]
    print(f"[OK] Created Organization ID: {org_id}")

    # 2. Register User under this organization
    username = f"analyst_{os.urandom(3).hex()}"
    email = f"{username}@forensight.org"
    password = "SuperPassword123"
    
    register_payload = {
        "email": email,
        "username": username,
        "organization_id": org_id,
        "password": password,
        "role": "investigator",
        "is_active": True
    }
    
    register_response = client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201
    user_data = register_response.json()
    assert user_data["username"] == username
    print(f"[OK] Registered User: {user_data['email']}")

    # 3. Login with registered user credentials
    login_payload = {
        "username": email,
        "password": password
    }
    login_response = client.post("/api/v1/auth/login", data=login_payload)
    assert login_response.status_code == 200
    token_data = login_response.json()
    token = token_data["access_token"]
    print(f"[OK] Logged in successfully. Token generated: {token[:20]}...")

    # 4. Fetch current user profile (/me)
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.json()
    print(f"[OK] Fetched user profile successfully: {me_data['username']}")

    # 5. List organizations (restricted endpoint, requires JWT)
    list_orgs_response = client.get("/api/v1/organizations/", headers=headers)
    assert list_orgs_response.status_code == 200
    print(f"[OK] Listed tenant organizations successfully.")
    
    return headers, org_id, token

def test_cases_and_evidence_flow(client, auth_headers, org_id):
    print("\nTesting Cases and Evidence (Upload + MinIO + Duplicate checks) REST Flows...")

    # 1. Create a Case
    case_title = f"Ransomware Incident - {os.urandom(2).hex()}"
    case_payload = {
        "title": case_title,
        "description": "Investigating locked workstation files and malicious registry entries.",
        "status": "open"
    }
    case_response = client.post("/api/v1/cases/", json=case_payload, headers=auth_headers)
    assert case_response.status_code == 201
    case_data = case_response.json()
    case_id = case_data["id"]
    print(f"[OK] Created Case ID: {case_id} ('{case_data['title']}')")

    # 2. List Cases (should include the new case)
    list_cases_response = client.get("/api/v1/cases/", headers=auth_headers)
    assert list_cases_response.status_code == 200
    cases_list = list_cases_response.json()
    assert any(c["id"] == case_id for c in cases_list)
    print(f"[OK] Listed cases successfully. Total cases: {len(cases_list)}")

    # 3. Get Case Details
    details_response = client.get(f"/api/v1/cases/{case_id}", headers=auth_headers)
    assert details_response.status_code == 200
    details = details_response.json()
    assert details["title"] == case_title
    print(f"[OK] Fetched Case details successfully.")

    # 4. Upload Evidence (Mock Windows security.evtx log file)
    dummy_file_content = b"Windows Event Log Binary Header [DUMMY FORENSIC EVTX]"
    dummy_file = io.BytesIO(dummy_file_content)
    
    upload_response = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        files={"file": ("security.evtx", dummy_file, "application/octet-stream")},
        headers=auth_headers
    )
    assert upload_response.status_code == 202
    evidence_data = upload_response.json()
    evidence_id = evidence_data["id"]
    assert evidence_data["filename"] == "security.evtx"
    assert evidence_data["file_type"] == "evtx"
    assert evidence_data["status"] == "queued"
    print(f"[OK] Uploaded Evidence successfully. File: {evidence_data['filename']} | MinIO Path: {evidence_data['minio_object_name']}")

    # 5. Check Duplicate Upload Protection (should return 409 Conflict)
    dummy_file.seek(0)
    duplicate_response = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        files={"file": ("security.evtx", dummy_file, "application/octet-stream")},
        headers=auth_headers
    )
    assert duplicate_response.status_code == 409
    print(f"[OK] Duplicate check passed. Refused upload with 409 Conflict.")

    # 6. List Case Evidence (should return 1 file metadata)
    list_evidence_response = client.get(f"/api/v1/cases/{case_id}/evidence", headers=auth_headers)
    assert list_evidence_response.status_code == 200
    evidence_list = list_evidence_response.json()
    assert len(evidence_list) == 1
    assert evidence_list[0]["id"] == evidence_id
    print(f"[OK] Listed case evidence metadata successfully.")

    # 7. Get Evidence specification details
    ev_detail_response = client.get(f"/api/v1/evidence/{evidence_id}", headers=auth_headers)
    assert ev_detail_response.status_code == 200
    ev_detail = ev_detail_response.json()
    assert ev_detail["sha256"] == evidence_data["sha256"]
    print(f"[OK] Fetched evidence detail specification successfully.")
    
    return case_id

def test_data_isolation(client, case_id):
    print("\nTesting Tenant Data Isolation Enforcements...")
    
    # 1. Create a second completely separate organization and user (Tenant B)
    org_name_b = f"Tenant B Lab - {os.urandom(4).hex()}"
    org_response = client.post("/api/v1/organizations/", json={"name": org_name_b})
    org_id_b = org_response.json()["id"]

    username_b = f"analyst_b_{os.urandom(3).hex()}"
    email_b = f"{username_b}@forensight.org"
    password_b = "TenantBPassword123"
    
    client.post("/api/v1/auth/register", json={
        "email": email_b,
        "username": username_b,
        "organization_id": org_id_b,
        "password": password_b,
        "role": "investigator",
        "is_active": True
    })

    login_response = client.post("/api/v1/auth/login", data={"username": email_b, "password": password_b})
    token_b = login_response.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    
    # 2. Try to view Tenant A's case using Tenant B's JWT (should return 404 Not Found / access denied)
    unauthorized_lookup = client.get(f"/api/v1/cases/{case_id}", headers=headers_b)
    assert unauthorized_lookup.status_code == 404
    print("[OK] Tenant Isolation check passed: Tenant B refused access to Tenant A's case details.")

    # 3. Try to list cases under Tenant B's session (should return empty list, not Tenant A's cases)
    list_cases_b = client.get("/api/v1/cases/", headers=headers_b)
    assert list_cases_b.status_code == 200
    assert len(list_cases_b.json()) == 0
    print("[OK] Tenant Isolation check passed: Tenant B listed 0 cases.")

if __name__ == "__main__":
    print("Starting local API REST endpoints integration tests...")
    try:
        with TestClient(app) as test_client:
            test_root_endpoint(test_client)
            headers, org_id, token = test_organization_and_auth_flow(test_client)
            case_id = test_cases_and_evidence_flow(test_client, headers, org_id)
            test_data_isolation(test_client, case_id)
        print("\nALL API ENDPOINTS INTEGRATION CHECKS PASSED PERFECTLY!")
    except Exception as e:
        print(f"\nAPI checks failed: {e}")
