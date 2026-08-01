"""
Processing Pipeline — ForenSight AI
======================================
On Windows, Celery workers fail due to the scapy cache permission bug.
This module processes evidence directly in a FastAPI background thread
using asyncio, which is reliable on all platforms.

The pipeline runs the full chain:
  parse → neo4j sync → anomaly detection → embeddings → correlations
"""

import asyncio
import logging
import os
import tempfile
import threading
from bson import ObjectId

from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.schemas.evidence import EvidenceStatus

logger = logging.getLogger(__name__)

# Fix scapy cache before any import
_scapy_cache = os.path.join(tempfile.gettempdir(), 'scapy_cache_forensight')
os.makedirs(_scapy_cache, exist_ok=True)
os.environ.setdefault('SCAPY_CACHE_DIR', _scapy_cache)


async def _run_full_pipeline(evidence_id: str, org_id: str):
    """
    Full evidence processing pipeline — runs async in a background task.
    parse → neo4j → anomaly detection → embeddings → correlations
    """
    from backend.app.repositories.event_repository import EventRepository
    from backend.app.repositories.graph_repository import GraphRepository
    from backend.app.db.minio import minio_client
    from backend.app.config import settings
    from backend.app.parsers import get_parser

    # 1. Fetch evidence
    evidence = await EvidenceRepository.get_by_id(evidence_id, org_id)
    if not evidence:
        logger.error(f"Evidence {evidence_id} not found")
        return

    logger.info(f"[PIPELINE] Starting: {evidence['filename']} ({evidence['file_type']})")
    await EvidenceRepository.update_status(evidence_id, org_id, EvidenceStatus.PARSING.value)

    try:
        # 2. Download from MinIO — ensure client is ready
        from backend.app.db.minio import minio_client, connect_to_minio
        if minio_client.client is None:
            connect_to_minio()
        response = minio_client.client.get_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=evidence["minio_object_name"]
        )
        file_content = response.read()
        response.close()
        response.release_conn()
        logger.info(f"[PIPELINE] Downloaded {len(file_content):,} bytes")

        # 3. Parse
        parser = get_parser(evidence["file_type"])
        events = parser.parse(file_content, filename=evidence["filename"])
        logger.info(f"[PIPELINE] Parsed {len(events)} events")

        # 4. Enrich with case/org metadata
        case_oid = ObjectId(str(evidence["case_id"]))
        org_oid  = ObjectId(org_id)
        ev_oid   = ObjectId(evidence_id)

        enriched = []
        for ev in events:
            ev.update({
                "case_id":        case_oid,
                "evidence_id":    ev_oid,
                "organization_id": org_oid,
            })
            enriched.append(ev)

        # 5. Bulk insert to MongoDB
        if enriched:
            count = await EventRepository.bulk_create(enriched)
            logger.info(f"[PIPELINE] Inserted {count} events to MongoDB")

            # 6. Sync to Neo4j
            synced = await GraphRepository.bulk_import_events(enriched)
            if synced == 0:
                logger.warning(f"[PIPELINE] ⚠️ Neo4j sync returned 0 — driver may be unavailable or all events lacked subject/object fields. Graph view will be empty.")
            else:
                logger.info(f"[PIPELINE] Synced {synced} events to Neo4j")

        # 7. Mark parsed
        await EvidenceRepository.update_status(evidence_id, org_id, EvidenceStatus.PARSED.value)
        logger.info(f"[PIPELINE] Status → PARSED")

        # 8. Anomaly detection
        case_id_str = str(evidence["case_id"])
        try:
            from backend.app.services.intelligence.anomaly.evaluator import ensemble_predict
            import numpy as np
            from collections import Counter
            from backend.app.db.mongodb import db_client

            evs = await EventRepository.list_by_case(case_id_str, org_id, limit=5000)
            n = len(evs)
            if n >= 5:
                SEV = {'info': 0.0, 'low': 0.25, 'medium': 0.5, 'high': 0.75, 'critical': 1.0}
                sc = Counter(e.get('subject', '') for e in evs)
                oc = Counter(e.get('object', '')  for e in evs)
                ac = Counter(e.get('action', '')  for e in evs)

                rows = []
                for e in evs:
                    ts = e.get('timestamp')
                    rows.append([
                        ts.hour if ts and hasattr(ts, 'hour') else 12,
                        1.0 if ts and ts.weekday() >= 5 else 0.0,
                        sc[e.get('subject', '')] / n,
                        oc[e.get('object', '')]  / n,
                        ac[e.get('action', '')]  / n,
                        SEV.get((e.get('severity') or 'info').lower(), 0.0),
                    ])

                X = np.array(rows, dtype=float)
                result = ensemble_predict(X)
                flags, scores = result['flags'], result['scores']

                ops = [
                    db_client.db['events'].update_one(
                        {'_id': evs[i]['_id']},
                        {'$set': {'is_anomaly': bool(flags[i]), 'anomaly_score': float(scores[i])}}
                    )
                    for i in range(n)
                ]
                await asyncio.gather(*ops)
                logger.info(f"[PIPELINE] Anomalies: {sum(flags)}/{n} flagged")
        except Exception as ae:
            logger.warning(f"[PIPELINE] Anomaly detection error (non-fatal): {ae}")

        # 9. FAISS vector embeddings
        try:
            from backend.app.services.ai.vector_store import VectorStore
            await VectorStore.index_case_events(case_id_str, org_id)
            logger.info(f"[PIPELINE] FAISS index built")
        except Exception as ve:
            logger.warning(f"[PIPELINE] Embedding error (non-fatal): {ve}")

        # 10. Graph correlation rules
        try:
            from backend.app.services.graph.graph_queries import GraphCorrelationRules
            results = await GraphCorrelationRules.run_all_rules(case_id_str, org_id)
            logger.info(f"[PIPELINE] Correlations: {results}")
        except Exception as ce:
            logger.warning(f"[PIPELINE] Correlation error (non-fatal): {ce}")

        logger.info(f"[PIPELINE] ✅ Complete for {evidence['filename']}")

    except Exception as e:
        logger.error(f"[PIPELINE] ❌ Failed: {e}")
        await EvidenceRepository.update_status(
            evidence_id, org_id,
            status=EvidenceStatus.FAILED.value,
            error_message=str(e)[:500]
        )


class ProcessingPipeline:

    @staticmethod
    async def trigger_processing(evidence_id: str, org_id: str) -> bool:
        """
        Queue evidence for background processing.
        Runs the full pipeline in a FastAPI background task (no Celery needed).
        """
        try:
            await EvidenceRepository.update_status(
                evidence_id, org_id, status=EvidenceStatus.QUEUED.value
            )

            # Try Celery first — if it fails, fall back to direct background task
            celery_ok = False
            try:
                from backend.app.worker.parser_tasks import process_evidence_task
                task = process_evidence_task.delay(evidence_id, org_id)
                logger.info(f"[PIPELINE] Celery task dispatched: {task.id}")
                celery_ok = True
            except Exception as ce:
                logger.warning(f"[PIPELINE] Celery unavailable ({ce}), using direct processing")

            if not celery_ok:
                # Run directly in background using asyncio
                asyncio.ensure_future(_run_full_pipeline(evidence_id, org_id))
                logger.info(f"[PIPELINE] Direct background task started for {evidence_id}")

            return True

        except Exception as e:
            logger.error(f"[PIPELINE] Trigger failed: {e}")
            await EvidenceRepository.update_status(
                evidence_id, org_id,
                status=EvidenceStatus.FAILED.value,
                error_message=f"Pipeline trigger error: {e}"
            )
            return False
