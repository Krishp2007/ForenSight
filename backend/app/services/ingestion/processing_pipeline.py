"""
Processing Pipeline — ForenSight AI
======================================
Runs the full evidence processing chain entirely inside the FastAPI process
using asyncio background tasks — no Celery worker required.

Pipeline steps:
  1.  Fetch evidence metadata from MongoDB
  2.  Download raw file from MinIO
  3.  Parse → structured events list
  4.  Enrich with case / org / evidence IDs
  5.  Bulk insert events into MongoDB
  6.  Sync event graph nodes/edges to Neo4j
  7.  Mark evidence status → PARSED
  8.  Run ensemble anomaly detection (IsolationForest)
  9.  Build FAISS semantic search index
  10. Run Cypher graph correlation rules
"""

import asyncio
import logging
import os
import tempfile
from datetime import datetime
from bson import ObjectId

from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.schemas.evidence import EvidenceStatus

logger = logging.getLogger(__name__)

# Fix scapy Windows cache path before any parser imports scapy
_scapy_cache = os.path.join(tempfile.gettempdir(), "scapy_cache_forensight")
os.makedirs(_scapy_cache, exist_ok=True)
os.environ.setdefault("SCAPY_CACHE_DIR", _scapy_cache)


async def _run_full_pipeline(evidence_id: str, org_id: str) -> None:
    """
    Full async evidence processing pipeline.
    Runs as a FastAPI background task — always executes inside the live event loop.
    """
    from backend.app.repositories.event_repository import EventRepository
    from backend.app.repositories.graph_repository import GraphRepository
    from backend.app.db.minio import minio_client, connect_to_minio
    from backend.app.config import settings
    from backend.app.parsers import get_parser

    # ── 1. Fetch evidence ────────────────────────────────────────────────────
    evidence = await EvidenceRepository.get_by_id(evidence_id, org_id)
    if not evidence:
        logger.error(f"[PIPELINE] Evidence {evidence_id} not found — aborting.")
        return

    filename = evidence.get("filename", evidence_id)
    logger.info(f"[PIPELINE] ▶ Starting: {filename} ({evidence.get('file_type')})")
    await EvidenceRepository.update_status(evidence_id, org_id, EvidenceStatus.PARSING.value)

    try:
        # ── 2. Download from MinIO ───────────────────────────────────────────
        if minio_client.client is None:
            connect_to_minio()
        response = minio_client.client.get_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=evidence["minio_object_name"],
        )
        file_content = response.read()
        response.close()
        response.release_conn()
        logger.info(f"[PIPELINE] Downloaded {len(file_content):,} bytes")

        # ── 3. Parse ─────────────────────────────────────────────────────────
        parser = get_parser(evidence["file_type"])
        events = parser.parse(file_content, filename=filename)
        logger.info(f"[PIPELINE] Parsed {len(events)} events")

        # ── 4. Enrich ────────────────────────────────────────────────────────
        case_oid = ObjectId(str(evidence["case_id"]))
        org_oid  = ObjectId(org_id)
        ev_oid   = ObjectId(evidence_id)
        for ev in events:
            ev.update({
                "case_id":         case_oid,
                "evidence_id":     ev_oid,
                "organization_id": org_oid,
            })

        # ── 5. MongoDB bulk insert ───────────────────────────────────────────
        if events:
            count = await EventRepository.bulk_create(events)
            logger.info(f"[PIPELINE] Inserted {count} events into MongoDB")

            # ── 6. Neo4j sync ────────────────────────────────────────────────
            synced = await GraphRepository.bulk_import_events(events)
            if synced == 0:
                logger.warning(
                    "[PIPELINE] ⚠️  Neo4j sync returned 0 — "
                    "driver unavailable or all events missing subject/object. "
                    "Graph will be empty until you click Re-process."
                )
            else:
                logger.info(f"[PIPELINE] Synced {synced} events to Neo4j")

        # ── 7. Mark PARSED ───────────────────────────────────────────────────
        await EvidenceRepository.update_status(evidence_id, org_id, EvidenceStatus.PARSED.value)
        logger.info(f"[PIPELINE] ✅ Status → PARSED for {filename}")

        case_id_str = str(evidence["case_id"])

        # ── 8. Anomaly detection ─────────────────────────────────────────────
        try:
            from backend.app.services.intelligence.anomaly.evaluator import ensemble_predict
            from backend.app.db.mongodb import db_client
            import numpy as np
            from collections import Counter

            evs = await EventRepository.list_by_case(case_id_str, org_id, limit=5000)
            n = len(evs)
            if n >= 5:
                SEV = {"info": 0.0, "low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}
                sc = Counter(e.get("subject", "") for e in evs)
                oc = Counter(e.get("object",  "") for e in evs)
                ac = Counter(e.get("action",  "") for e in evs)
                rows = []
                for e in evs:
                    ts = e.get("timestamp")
                    rows.append([
                        ts.hour      if ts and hasattr(ts, "hour")    else 12,
                        1.0          if ts and ts.weekday() >= 5      else 0.0,
                        sc[e.get("subject", "")] / n,
                        oc[e.get("object",  "")] / n,
                        ac[e.get("action",  "")] / n,
                        SEV.get((e.get("severity") or "info").lower(), 0.0),
                    ])
                X = np.array(rows, dtype=float)
                res = ensemble_predict(X)
                flags, scores = res["flags"], res["scores"]
                ops = [
                    db_client.db["events"].update_one(
                        {"_id": evs[i]["_id"]},
                        {"$set": {"is_anomaly": bool(flags[i]),
                                  "anomaly_score": float(scores[i])}},
                    )
                    for i in range(n)
                ]
                await asyncio.gather(*ops)
                logger.info(f"[PIPELINE] Anomalies: {sum(flags)}/{n} flagged")
            else:
                logger.info(f"[PIPELINE] Only {n} events — skipping anomaly detection")
        except Exception as ae:
            logger.warning(f"[PIPELINE] Anomaly detection error (non-fatal): {ae}")

        # ── 9. FAISS embeddings ──────────────────────────────────────────────
        try:
            from backend.app.services.ai.vector_store import VectorStore
            await VectorStore.index_case_events(case_id_str, org_id)
            logger.info("[PIPELINE] FAISS index built")
        except Exception as ve:
            logger.warning(f"[PIPELINE] Embedding error (non-fatal): {ve}")

        # ── 10. Graph correlation rules ──────────────────────────────────────
        try:
            from backend.app.services.graph.graph_queries import GraphCorrelationRules
            corr = await GraphCorrelationRules.run_all_rules(case_id_str, org_id)
            logger.info(f"[PIPELINE] Correlations: {corr}")
        except Exception as ce:
            logger.warning(f"[PIPELINE] Correlation error (non-fatal): {ce}")

        logger.info(f"[PIPELINE] 🏁 Complete for {filename}")

    except Exception as e:
        logger.error(f"[PIPELINE] ❌ Failed for {filename}: {e}", exc_info=True)
        await EvidenceRepository.update_status(
            evidence_id, org_id,
            status=EvidenceStatus.FAILED.value,
            error_message=str(e)[:500],
        )


class ProcessingPipeline:
    """
    Trigger evidence processing as a FastAPI BackgroundTask.

    Why NOT Celery here:
      - Celery dispatches to Redis; if no worker is running the task sits
        in the queue forever → status stays 'queued'.
      - asyncio background tasks run inside the FastAPI process immediately,
        require zero extra processes, and work on Windows without any DLL issues.
      - For scale-out, swap _run_full_pipeline back to a Celery task later.
    """

    @staticmethod
    def run_in_background(background_tasks, evidence_id: str, org_id: str) -> None:
        """
        Schedule the pipeline via FastAPI BackgroundTasks.
        Call this from the API endpoint — pass `background_tasks: BackgroundTasks`.
        """
        background_tasks.add_task(_run_full_pipeline, evidence_id, org_id)
        logger.info(f"[PIPELINE] Background task scheduled for evidence {evidence_id}")

    @staticmethod
    async def trigger_processing(evidence_id: str, org_id: str) -> bool:
        """
        Legacy async trigger kept for backward compat (reprocess endpoint).
        Schedules the pipeline directly via asyncio.create_task so it runs
        immediately inside the current event loop — no Celery needed.
        """
        try:
            await EvidenceRepository.update_status(
                evidence_id, org_id, status=EvidenceStatus.QUEUED.value
            )
            # create_task schedules on the running loop immediately — never blocks
            asyncio.create_task(_run_full_pipeline(evidence_id, org_id))
            logger.info(f"[PIPELINE] asyncio.create_task scheduled for {evidence_id}")
            return True
        except Exception as e:
            logger.error(f"[PIPELINE] Trigger failed: {e}")
            await EvidenceRepository.update_status(
                evidence_id, org_id,
                status=EvidenceStatus.FAILED.value,
                error_message=f"Pipeline trigger error: {e}",
            )
            return False
