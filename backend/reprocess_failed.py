"""Re-process all failed/queued evidence directly."""
import asyncio, sys, os, tempfile

os.environ['SCAPY_CACHE_DIR'] = os.path.join(tempfile.gettempdir(), 'scapy_cache_forensight')
os.makedirs(os.environ['SCAPY_CACHE_DIR'], exist_ok=True)
sys.path.insert(0, 'd:/ForenSight/ForenSight')

from backend.app.db.mongodb import connect_to_mongo, db_client
from backend.app.db.neo4j import connect_to_neo4j
from backend.app.db.minio import connect_to_minio, minio_client
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.repositories.event_repository import EventRepository
from backend.app.schemas.evidence import EvidenceStatus
from backend.app.parsers import get_parser
from backend.app.config import settings
from bson import ObjectId
import numpy as np
from collections import Counter

SEV = {'info':0.0,'low':0.25,'medium':0.5,'high':0.75,'critical':1.0}

async def process(evidence_id, org_id):
    ev = await EvidenceRepository.get_by_id(evidence_id, org_id)
    if not ev: print(f"  NOT FOUND: {evidence_id}"); return

    print(f"\nProcessing: {ev['filename']} ({ev['file_type']})")
    await EvidenceRepository.update_status(evidence_id, org_id, EvidenceStatus.PARSING.value)

    try:
        resp = minio_client.client.get_object(settings.MINIO_BUCKET_NAME, ev["minio_object_name"])
        content = resp.read(); resp.close(); resp.release_conn()
        print(f"  Downloaded: {len(content):,} bytes")

        parser = get_parser(ev["file_type"])
        events = parser.parse(content, filename=ev["filename"])
        print(f"  Parsed: {len(events)} events")

        enriched = []
        for e in events:
            e.update({"case_id": ObjectId(str(ev["case_id"])), "evidence_id": ObjectId(evidence_id), "organization_id": ObjectId(org_id)})
            enriched.append(e)

        if enriched:
            count = await EventRepository.bulk_create(enriched)
            print(f"  MongoDB: {count} events inserted")
            from backend.app.repositories.graph_repository import GraphRepository
            await GraphRepository.bulk_import_events(enriched)
            print(f"  Neo4j: synced")

        await EvidenceRepository.update_status(evidence_id, org_id, EvidenceStatus.PARSED.value)
        print(f"  Status -> PARSED ✅")

        # Anomaly detection
        case_id_str = str(ev["case_id"])
        all_evs = await EventRepository.list_by_case(case_id_str, org_id, limit=5000)
        n = len(all_evs)
        if n >= 5:
            sc = Counter(e.get('subject','') for e in all_evs)
            oc = Counter(e.get('object','') for e in all_evs)
            ac = Counter(e.get('action','') for e in all_evs)
            rows = []
            for e in all_evs:
                ts = e.get('timestamp')
                rows.append([ts.hour if ts and hasattr(ts,'hour') else 12, 1.0 if ts and ts.weekday()>=5 else 0.0,
                    sc[e.get('subject','')] / n, oc[e.get('object','')] / n, ac[e.get('action','')] / n,
                    SEV.get((e.get('severity') or 'info').lower(), 0.0)])
            X = np.array(rows, dtype=float)
            from backend.app.services.intelligence.anomaly.evaluator import ensemble_predict
            result = ensemble_predict(X)
            flags, scores = result['flags'], result['scores']
            ops = [db_client.db['events'].update_one({'_id': all_evs[i]['_id']}, {'$set': {'is_anomaly': bool(flags[i]), 'anomaly_score': float(scores[i])}}) for i in range(n)]
            await asyncio.gather(*ops)
            print(f"  Anomalies: {sum(flags)}/{n} flagged")

        # Graph correlations
        from backend.app.services.graph.graph_queries import GraphCorrelationRules
        results = await GraphCorrelationRules.run_all_rules(case_id_str, org_id)
        print(f"  Correlations: {results}")

        # FAISS
        from backend.app.services.ai.vector_store import VectorStore
        await VectorStore.index_case_events(case_id_str, org_id)
        print(f"  FAISS index: built")

    except Exception as e:
        print(f"  ERROR: {e}")
        await EvidenceRepository.update_status(evidence_id, org_id, EvidenceStatus.FAILED.value, error_message=str(e)[:300])

async def run():
    print("Connecting...")
    await connect_to_mongo()
    await connect_to_neo4j()
    connect_to_minio()
    print("Connected.\n")

    stuck = await db_client.db['evidence'].find({'status': {'$in': ['failed','queued','uploaded']}}).to_list(50)
    print(f"Found {len(stuck)} evidence to reprocess")
    for e in stuck:
        await process(str(e['_id']), str(e['organization_id']))

    print("\n=== DONE ===")

asyncio.run(run())
