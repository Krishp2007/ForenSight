"""Process stuck evidence directly (no Celery) — bypasses scapy cache issue."""
import asyncio, sys, os

os.environ['SCAPY_CACHE_DIR'] = os.path.join(os.environ.get('TEMP','C:\\Temp'), 'scapy_cache')
os.makedirs(os.environ['SCAPY_CACHE_DIR'], exist_ok=True)

sys.path.insert(0, 'd:/ForenSight/ForenSight')

from backend.app.db.mongodb import connect_to_mongo, db_client
from backend.app.db.neo4j import connect_to_neo4j
from backend.app.db.minio import connect_to_minio
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.repositories.event_repository import EventRepository
from backend.app.schemas.evidence import EvidenceStatus
from backend.app.parsers import get_parser
from backend.app.config import settings
from backend.app.db.minio import minio_client
from bson import ObjectId

async def process_evidence(evidence_id: str, org_id: str):
    evidence = await EvidenceRepository.get_by_id(evidence_id, org_id)
    if not evidence:
        print(f"  ERROR: Evidence {evidence_id} not found")
        return

    print(f"  Processing: {evidence['filename']} (type={evidence['file_type']})")
    await EvidenceRepository.update_status(evidence_id, org_id, EvidenceStatus.PARSING.value)

    try:
        # Get file from MinIO
        response = minio_client.client.get_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=evidence["minio_object_name"]
        )
        file_content = response.read()
        response.close()
        response.release_conn()
        print(f"    Downloaded {len(file_content)} bytes from MinIO")

        # Parse
        parser = get_parser(evidence["file_type"])
        events = parser.parse(file_content, filename=evidence["filename"])
        print(f"    Parsed {len(events)} events")

        # Enrich
        enriched = []
        for ev in events:
            ev.update({
                "case_id": ObjectId(str(evidence["case_id"])),
                "evidence_id": ObjectId(evidence_id),
                "organization_id": ObjectId(org_id)
            })
            enriched.append(ev)

        # Bulk insert to MongoDB
        if enriched:
            count = await EventRepository.bulk_create(enriched)
            print(f"    Inserted {count} events to MongoDB")

            # Sync to Neo4j
            from backend.app.repositories.graph_repository import GraphRepository
            await GraphRepository.bulk_import_events(enriched)
            print(f"    Synced to Neo4j graph")

        await EvidenceRepository.update_status(evidence_id, org_id, EvidenceStatus.PARSED.value)
        print(f"    Status -> PARSED")

    except Exception as e:
        print(f"    ERROR: {e}")
        await EvidenceRepository.update_status(
            evidence_id, org_id,
            status=EvidenceStatus.FAILED.value,
            error_message=str(e)
        )

async def run():
    print("Connecting to databases...")
    await connect_to_mongo()
    await connect_to_neo4j()
    connect_to_minio()
    print("Connected.\n")

    stuck = await db_client.db['evidence'].find(
        {'status': {'$in': ['uploaded', 'queued']}}
    ).to_list(50)

    print(f"Found {len(stuck)} evidence records to process\n")

    for e in stuck:
        eid = str(e['_id'])
        oid = str(e['organization_id'])
        await process_evidence(eid, oid)
        print()

    # Run anomaly detection
    print("Running anomaly detection...")
    cases = list(set(str(e['case_id']) for e in stuck))
    for cid in cases:
        oid = str(stuck[0]['organization_id'])
        try:
            from backend.app.services.intelligence.anomaly.evaluator import ensemble_predict
            from backend.app.repositories.event_repository import EventRepository
            import numpy as np
            from collections import Counter

            events = await EventRepository.list_by_case(cid, oid, limit=5000)
            n = len(events)
            if n >= 5:
                subjects = [ev.get('subject','') for ev in events]
                objects  = [ev.get('object','')  for ev in events]
                actions  = [ev.get('action','')  for ev in events]
                sc = Counter(subjects); oc = Counter(objects); ac = Counter(actions)
                SEV = {'info':0,'low':0.25,'medium':0.5,'high':0.75,'critical':1.0}
                rows = []
                for ev in events:
                    ts = ev.get('timestamp')
                    rows.append([
                        ts.hour if ts and hasattr(ts,'hour') else 12,
                        1.0 if ts and ts.weekday()>=5 else 0.0,
                        sc[ev.get('subject','')] / n,
                        oc[ev.get('object','')] / n,
                        ac[ev.get('action','')] / n,
                        SEV.get((ev.get('severity') or 'info').lower(), 0.0)
                    ])
                X = np.array(rows, dtype=float)
                result = ensemble_predict(X)
                flags = result['flags']; scores = result['scores']
                import asyncio as aio
                ops = [db_client.db['events'].update_one(
                    {'_id': events[i]['_id']},
                    {'$set': {'is_anomaly': bool(flags[i]), 'anomaly_score': float(scores[i])}}
                ) for i in range(n)]
                await aio.gather(*ops)
                flagged = sum(flags)
                print(f"  Anomaly detection: {flagged}/{n} events flagged")
        except Exception as e:
            print(f"  Anomaly detection error (non-fatal): {e}")

    print("\nAll done! Refresh the UI.")

asyncio.run(run())
