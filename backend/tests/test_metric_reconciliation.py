import asyncio
import os
import sys
import pytest
from bson import ObjectId

# Add backend root to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, backend_dir)

from backend.app.db.mongodb import connect_to_mongo, db_client
from backend.app.repositories.event_repository import EventRepository
from backend.app.repositories.evidence_repository import EvidenceRepository

@pytest.mark.asyncio
async def test_metric_reconciliation():
    await connect_to_mongo()
    
    # 1. Fetch test cases
    cases = await db_client.db["cases"].find({}).to_list(10)
    assert len(cases) > 0, "No cases found to test metric reconciliation"
    
    for case in cases:
        case_id = str(case["_id"])
        org_id = str(case["organization_id"])
        
        # Fetch case-level stats via canonical Metrics Engine
        case_stats = await EventRepository.count_stats(case_id, org_id)
        
        ev_items = await EvidenceRepository.list_by_case(case_id, org_id)
        
        if len(ev_items) == 1:
            # For 1 evidence file, Case Scope MUST match Evidence Scope 100%
            ev_id = str(ev_items[0]["_id"])
            ev_stats = await EventRepository.count_stats(case_id, org_id, evidence_id=ev_id)
            
            assert case_stats["total"] == ev_stats["total"], \
                f"Mismatch in Total Events: Case={case_stats['total']} vs Evidence={ev_stats['total']}"
            assert case_stats["anomalies"] == ev_stats["anomalies"], \
                f"Mismatch in Anomalies: Case={case_stats['anomalies']} vs Evidence={ev_stats['anomalies']}"
            assert case_stats["critical"] == ev_stats["critical"], \
                f"Mismatch in Critical: Case={case_stats['critical']} vs Evidence={ev_stats['critical']}"
                
            print(f"✅ Metric Reconciliation Passed for Single-File Case '{case.get('title')}': {case_stats}")

if __name__ == "__main__":
    asyncio.run(test_metric_reconciliation())
