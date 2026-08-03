r"""
ForenSight AI - Async Celery Pipeline Test
===============================================
This test verifies the actual async worker pipeline behavior by triggering Celery
tasks via the broker (.delay) and polling the database and REST endpoints.

Prerequisites:
  1. Docker containers running (MongoDB, Redis, Neo4j, MinIO)
  2. Celery worker running in the background:
     CMD: celery -A backend.app.worker.celery_app worker --loglevel=info -P threads

Run: .\.venv\Scripts\python.exe .\test_async_pipeline.py
"""

import sys
import os
import io
import json
import uuid
import time
import hashlib
import asyncio
import redis

# Adjust path to import backend modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.worker.parser_tasks import process_evidence_task
from backend.app.db.mongodb import db_client
from backend.app.db.minio import minio_client
from backend.app.config import settings

# Polling configurations (PR Suggestions 2 & 3)
ASYNC_TIMEOUT = 45.0
POLL_INTERVAL = 2.0

# Sample forensic logs (CSV)
CSV_EVIDENCE = (
    "Timestamp,Event_Type,Subject,Action,Object,Severity\n"
    "2026-07-15 01:15:00,auth_event,admin_user,logged_in,workstation-07,info\n"
    "2026-07-15 01:20:00,process_creation,explorer.exe,spawned,cmd.exe,low\n"
    "2026-07-15 01:22:00,process_creation,cmd.exe,spawned,powershell.exe -enc ZABvAHcAbgBsAG8AYQBk,critical\n"
    "2026-07-15 01:25:00,network_connection,powershell.exe,connected_to,185.220.101.45:4444,high\n"
    "2026-07-15 01:26:00,file_modification,powershell.exe,created,C:\\temp\\payload.exe,high\n"
    "2026-07-15 01:28:00,registry_change,payload.exe,modified,HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\Run,critical\n"
    "2026-07-15 01:30:00,process_creation,payload.exe,spawned,vssadmin.exe delete shadows /all,critical\n"
    "2026-07-15 01:35:00,network_connection,payload.exe,connected_to,10.0.0.200:445,medium\n"
    "2026-07-15 01:40:00,file_modification,payload.exe,created,C:\\Users\\admin\\Documents\\exfil_data.zip,high\n"
    "2026-07-15 01:42:00,network_connection,payload.exe,connected_to,185.220.101.45:443,high\n"
    "2026-07-15 02:00:00,auth_event,admin_user,logged_out,workstation-07,info\n"
).encode("utf-8")


async def cleanup_db_after_async_test(case_id: str, org_id: str):
    """Prunes DB trace documents created by the async validation run."""
    from bson import ObjectId
    db = db_client.db
    await db["events"].delete_many({"case_id": ObjectId(case_id)})
    await db["evidence"].delete_many({"case_id": ObjectId(case_id)})
    await db["cases"].delete_one({"_id": ObjectId(case_id)})
    await db["organizations"].delete_one({"_id": ObjectId(org_id)})
    await db["users"].delete_many({"organization_id": ObjectId(org_id)})
    print("  🧹 MongoDB clean-up completed.")


def run_async_celery_integration_check():
    print("=" * 70)
    print("   FORENSIGHT AI — ASYNC CELERY WORKER PIPELINE TEST")
    print("=" * 70)

    unique = uuid.uuid4().hex[:8]
    case_id = None
    org_id = None
    csv_sha256 = None
    headers = {}

    with TestClient(app) as client:
        try:
            # Step 1. Organization & User Registration
            org_res = client.post("/api/v1/organizations/", json={"name": f"Async Org {unique}"})
            assert org_res.status_code == 201
            org_id = org_res.json()["id"]

            email = f"async_investigator_{unique}@forensight.org"
            reg_res = client.post("/api/v1/auth/register", json={
                "email": email, "username": f"async_analyst_{unique}",
                "organization_id": org_id, "password": "AsyncPassWord123!",
                "role": "investigator", "is_active": True
            })
            assert reg_res.status_code == 201

            # Login
            login_res = client.post("/api/v1/auth/login", data={"username": email, "password": "AsyncPassWord123!"})
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Step 2. Create Case
            case_res = client.post("/api/v1/cases/", json={
                "title": f"Async Queue Verification {unique}",
                "description": "Validating Redis broker and concurrent Celery processing loops."
            }, headers=headers)
            assert case_res.status_code == 201
            case_id = case_res.json()["id"]
            print(f"  🏢 Test Case created: ID={case_id}")

            # Step 3. Upload raw CSV payload
            upload_res = client.post(
                f"/api/v1/cases/{case_id}/evidence",
                files={"file": ("async_evidence.csv", io.BytesIO(CSV_EVIDENCE), "text/csv")},
                headers=headers
            )
            assert upload_res.status_code == 202
            evidence_id = upload_res.json()["id"]
            csv_sha256 = upload_res.json()["sha256"]
            print(f"  📤 Evidence uploaded to queue. ID={evidence_id}")

            # Verify MinIO Storage
            stat = minio_client.client.stat_object(settings.MINIO_BUCKET_NAME, f"{org_id}/{case_id}/{csv_sha256}.csv")
            assert stat.size == len(CSV_EVIDENCE)
            print("  💾 Payload exists on MinIO") # Fixed typo (PR Suggestion 10)

            # Pre-Flight: Check if there are active Celery worker instances online
            print("\n🔍 Checking Celery worker status...")
            from backend.app.worker.celery_app import celery_app
            
            # Query active worker stats
            try:
                inspect = celery_app.control.inspect(timeout=3.0)
                stats = inspect.stats()
                if not stats:
                    print("  ❌ ERROR: No running Celery workers detected!")
                    print("     Please start a Celery worker before running this test:")
                    print("     celery -A backend.app.worker.celery_app worker --loglevel=info -P threads")
                    raise RuntimeError("No active Celery workers online. Cannot run async environment checks.")
                print(f"  ✅ Celery workers online: {list(stats.keys())}")
            except Exception as err:
                if isinstance(err, RuntimeError):
                    raise err
                print(f"  ⚠️ Worker check warning (Broker lookup failed): {err}")

            # Redis Queue Size Inspection (PR Suggestion 8)
            redis_conn = None
            try:
                redis_conn = redis.from_url(settings.REDIS_URL)
                initial_len = redis_conn.llen("celery")
                print(f"  📥 Initial Redis queue length ('celery' list): {initial_len}")
            except Exception as e:
                initial_len = None
                print(f"  ⚠️ Could not query Redis queue size: {e}")

            # Step 4. Dispatch Celery Task Asynchronously via Redis Broker (.delay)
            print("\n🚀 Dispatching task to Celery worker: process_evidence_task.delay(...)")
            task = process_evidence_task.delay(evidence_id, org_id)
            print(f"  Task UUID: {task.id}")
            print(f"  Waiting for worker pipeline chain execution (Evidence Parser -> ML Anomaly -> FAISS Embeddings)...")

            if redis_conn and initial_len is not None:
                try:
                    post_len = redis_conn.llen("celery")
                    print(f"  📥 Post-delay Redis queue length ('celery' list): {post_len}")
                except Exception:
                    pass

            # Step 5. Poll database parameters and Celery task state until everything completes
            from celery.result import AsyncResult
            elapsed = 0
            success = False

            while elapsed < ASYNC_TIMEOUT:
                # Query Celery state backend directly (PR Suggestion 1 / 9)
                async_res = AsyncResult(task.id, app=celery_app)
                task_state = async_res.state

                # Query evidence endpoint status via API
                ev_check = client.get(f"/api/v1/cases/{case_id}/evidence", headers=headers)
                current_status = "unknown"
                if ev_check.status_code == 200:
                    evidence_list = ev_check.json()
                    if evidence_list:
                        current_status = evidence_list[0].get("status")

                print(f"  [{elapsed}s] Evidence status: '{current_status}' | Celery state: '{task_state}'")

                if current_status == "parsed":
                    # Check if ML anomaly detection succeeded and generated event embeddings
                    events_check = client.get(f"/api/v1/cases/{case_id}/events", headers=headers)
                    events = events_check.json()
                    
                    # Verify that anomaly scoring has been completed on the database records
                    has_anomalies = any("is_anomaly" in ev for ev in events) if events else False
                    
                    # Try semantic search (verifies FAISS vector indexing is complete)
                    search_res = client.get(f"/api/v1/cases/{case_id}/search?query=powershell", headers=headers)
                    search_complete = (search_res.status_code == 200 and len(search_res.json()) > 0)

                    if has_anomalies and search_complete:
                        print(f"\n✨ Success! Background Chain completely finished in {elapsed}s:")
                        print(f"    - Parsed events  : {len(events)}")
                        print(f"    - Anomalies run  : Yes (flagged objects detected)")
                        print(f"    - Embeddings Index: Yes (search results found)")
                        success = True
                        break
                    else:
                        print(f"    -> Waiting for ML anomaly detection / embedding index sync...")
                
                time.sleep(POLL_INTERVAL)
                elapsed += POLL_INTERVAL

            # Better diagnostics dump before raising AssertionError if timeout occurred (PR Suggestion 4)
            if not success:
                # Query parameters to print a traceback profile
                diag_ev = client.get(f"/api/v1/cases/{case_id}/evidence", headers=headers)
                ev_data = diag_ev.json() if diag_ev.status_code == 200 else f"HTTP Err ({diag_ev.status_code})"
                
                diag_events = client.get(f"/api/v1/cases/{case_id}/events", headers=headers)
                events_cnt = len(diag_events.json()) if diag_events.status_code == 200 else f"HTTP Err ({diag_events.status_code})"
                
                diag_search = client.get(f"/api/v1/cases/{case_id}/search?query=powershell", headers=headers)
                search_cnt = len(diag_search.json()) if diag_search.status_code == 200 else f"HTTP Err ({diag_search.status_code})"
                
                print("\n❌ PIPELINE TIMEOUT DIAGNOSTICS:")
                print(f"   - Task UUID      : {task.id}")
                print(f"   - Celery State   : {AsyncResult(task.id, app=celery_app).state}")
                print(f"   - Evidence State : {ev_data}")
                print(f"   - Events Count   : {events_cnt}")
                print(f"   - Search Count   : {search_cnt}")
                print(f"   - Elapsed Time   : {elapsed} seconds / Timeout: {ASYNC_TIMEOUT} seconds")

            # Assert Pipeline completed successfully
            assert success, "Async Celery pipeline test timed out or failed"

            # Triage and QA check
            copilot_res = client.post(
                f"/api/v1/cases/{case_id}/copilot",
                json={"question": "Which IP address contains network C2 indicators?"},
                headers=headers
            )
            assert copilot_res.status_code == 200
            qa_analysis = copilot_res.json()["analysis"]
            print("\n🤖 QA Copilot response lookup testing on Heuristics fallback:")
            print(f"   Prompt Question: 'Which IP address contains network C2 indicators?'")
            print(f"   Answer snippet : {qa_analysis.split('###')[1][:250].strip()}...")
            assert "185.220" in qa_analysis
            print("\n  ✅ QA Assistant local keyword answer contains exfil network indicators!")

        finally:
            # Unconditional cleanup inside finally block (PR Suggestion 5)
            if case_id and org_id:
                print("\n🧹 Initiating unconditional environment teardown...")
                try:
                    client.delete(f"/api/v1/cases/{case_id}/graph", headers=headers)
                except Exception as e:
                    print(f"  ⚠️ Graph deletion skipped: {e}")
                
                if csv_sha256:
                    try:
                        minio_client.client.remove_object(settings.MINIO_BUCKET_NAME, f"{org_id}/{case_id}/{csv_sha256}.csv")
                        print("  🗑️ Payloads deleted from MinIO bucket")
                    except Exception as e:
                        print(f"  ⚠️ MinIO object deletion skipped: {e}")
                
                try:
                    asyncio.run(cleanup_db_after_async_test(case_id, org_id))
                except Exception as e:
                    print(f"  ⚠️ MongoDB trace deletion skipped: {e}")

    print("\n" + "=" * 70)
    print("   ✅ CONCURRENT CELERY PIPELINE BACKEND INTEGRATION PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_async_celery_integration_check()
