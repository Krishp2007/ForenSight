"""
Processing Pipeline — ForenSight AI
======================================
Runs the full evidence processing chain entirely inside the FastAPI process
using asyncio background tasks — no Celery worker required.

Pipeline steps (critical path — affects parse timer):
  1.  Fetch evidence metadata from MongoDB
  2.  Download raw file from MinIO          (thread executor)
  3.  Parse → structured events list        (thread executor)
  4.  Enrich with case / org / evidence IDs
  5.  Bulk insert events into MongoDB
  6.  Mark evidence status → PARSED  ← UI timer stops here

Post-parsed background steps (do NOT block the timer):
  7.  Sync event graph nodes/edges to Neo4j
  8.  Run ensemble anomaly detection
  9.  Build FAISS semantic search index
  10. Run Cypher graph correlation rules
"""

import asyncio
import concurrent.futures
import logging
import os
import tempfile
from bson import ObjectId

from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.schemas.evidence import EvidenceStatus

logger = logging.getLogger(__name__)

# Fix scapy Windows cache path before any parser imports scapy
_scapy_cache = os.path.join(tempfile.gettempdir(), "scapy_cache_forensight")
os.makedirs(_scapy_cache, exist_ok=True)
os.environ.setdefault("SCAPY_CACHE_DIR", _scapy_cache)

# Shared multi-core thread pool executor for CPU-bound forensic parsing
_parse_executor = concurrent.futures.ThreadPoolExecutor(max_workers=min(32, (os.cpu_count() or 4) + 4))


async def _run_full_pipeline(evidence_id: str, org_id: str, file_bytes: Optional[bytes] = None) -> None:
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
    file_type = evidence.get("file_type", "json")
    logger.info(f"[PIPELINE] ▶ Starting: {filename} ({file_type})")
    await EvidenceRepository.update_status(evidence_id, org_id, EvidenceStatus.PARSING.value)

    loop = asyncio.get_running_loop()
    _t0 = loop.time()

    try:
        # ── 2. Obtain file content (use in-memory bytes if available, else download from S3)
        if file_bytes:
            file_content = file_bytes
            logger.info(f"[PIPELINE] ⏱ In-memory buffer used (0.0s S3 latency): {len(file_content):,} bytes")
        else:
            if minio_client.client is None:
                connect_to_minio()

            def _download():
                resp = minio_client.client.get_object(
                    bucket_name=settings.MINIO_BUCKET_NAME,
                    object_name=evidence["minio_object_name"],
                )
                data = resp.read()
                resp.close()
                resp.release_conn()
                return data

            file_content = await loop.run_in_executor(None, _download)
            logger.info(f"[PIPELINE] ⏱ Download: {loop.time()-_t0:.1f}s  {len(file_content):,} bytes")

        # ── 3. Parse (CPU-bound / blocking I/O → parallel thread executor) ───
        parser = get_parser(file_type)
        _t1 = loop.time()
        events = await loop.run_in_executor(
            _parse_executor,
            lambda: parser.parse(file_content, filename=filename),
        )


        logger.info(f"[PIPELINE] ⏱ Parse:    {loop.time()-_t1:.1f}s  {len(events)} events")

        # ── 4. Enrich ─────────────────────────────────────────────────────────
        case_oid = ObjectId(str(evidence["case_id"]))
        org_oid  = ObjectId(org_id)
        ev_oid   = ObjectId(evidence_id)
        for ev in events:
            ev.update({
                "case_id":         case_oid,
                "evidence_id":     ev_oid,
                "organization_id": org_oid,
            })

        # ── 5. MongoDB bulk insert ────────────────────────────────────────────
        _t2 = loop.time()
        if events:
            count = await EventRepository.bulk_create(events)
            logger.info(f"[PIPELINE] ⏱ MongoDB:  {loop.time()-_t2:.1f}s  {count} inserted")

        # ── 6. Mark PARSED — UI timer stops here ─────────────────────────────
        await EvidenceRepository.update_status(evidence_id, org_id, EvidenceStatus.PARSED.value)
        logger.info(f"[PIPELINE] ✅ PARSED in {loop.time()-_t0:.1f}s total — {filename}")

        # ── 7-10. Post-parse enrichment runs fully in background ──────────────
        case_id_str = str(evidence["case_id"])
        asyncio.create_task(_run_post_pipeline(
            events, case_id_str, org_id, loop
        ))

    except Exception as e:
        logger.error(f"[PIPELINE] ❌ Failed for {filename}: {e}", exc_info=True)
        await EvidenceRepository.update_status(
            evidence_id, org_id,
            status=EvidenceStatus.FAILED.value,
            error_message=str(e)[:500],
        )


async def _run_post_pipeline(events, case_id_str: str, org_id: str, loop) -> None:
    """
    Post-parse enrichment: Neo4j, anomaly detection, embeddings, correlations.
    Runs after PARSED is set — never blocks the main pipeline timer.
    All four run concurrently via asyncio.gather.
    """
    from backend.app.repositories.graph_repository import GraphRepository
    from backend.app.repositories.event_repository import EventRepository

    _tp = loop.time()

    async def _neo4j():
        try:
            _t = loop.time()
            synced = await GraphRepository.bulk_import_events(events)
            logger.info(f"[POST] ⏱ Neo4j:    {loop.time()-_t:.1f}s  {synced} synced")
        except Exception as e:
            logger.warning(f"[POST] Neo4j error (non-fatal): {e}")

    async def _anomaly():
        try:
            from backend.app.services.intelligence.anomaly.evaluator import ensemble_predict
            from backend.app.db.mongodb import db_client
            from pymongo import UpdateOne
            import numpy as np
            from collections import Counter

            # Cap at 2000 — O(n²) LOF gets very slow beyond this
            evs = await EventRepository.list_by_case(case_id_str, org_id, limit=2000)
            n = len(evs)
            if n < 1:
                return

            if n < 5:
                # For small sample sizes (n < 5), flag high/critical severity or tagged events as anomalies
                bulk_ops = [
                    UpdateOne(
                        {"_id": e["_id"]},
                        {"$set": {
                            "is_anomaly": e.get("severity") in ("critical", "high", "medium") or bool(e.get("mitre_techniques")),
                            "anomaly_score": 0.85 if e.get("severity") in ("critical", "high") else 0.4
                        }}
                    )
                    for e in evs
                ]
                await db_client.db["events"].bulk_write(bulk_ops, ordered=False)
                logger.info(f"[POST] ⏱ Anomaly (small sample n={n}): tagged events.")
                return

            SEV = {"info": 0.0, "low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}
            sc = Counter(e.get("subject", "") for e in evs)
            oc = Counter(e.get("object",  "") for e in evs)
            ac = Counter(e.get("action",  "") for e in evs)
            rows = [[
                ts.hour if (ts := e.get("timestamp")) and hasattr(ts, "hour") else 12,
                1.0 if ts and ts.weekday() >= 5 else 0.0,
                sc[e.get("subject", "")] / n,
                oc[e.get("object",  "")] / n,
                ac[e.get("action",  "")] / n,
                SEV.get((e.get("severity") or "info").lower(), 0.0),
            ] for e in evs]
            X = np.array(rows, dtype=float)

            _t = loop.time()
            res = await loop.run_in_executor(None, lambda: ensemble_predict(X))
            flags, scores = res["flags"], res["scores"]

            bulk_ops = [
                UpdateOne(
                    {"_id": evs[i]["_id"]},
                    {"$set": {"is_anomaly": bool(flags[i]), "anomaly_score": float(scores[i])}},
                )
                for i in range(n)
            ]
            await db_client.db["events"].bulk_write(bulk_ops, ordered=False)
            logger.info(f"[POST] ⏱ Anomaly:  {loop.time()-_t:.1f}s  {sum(flags)}/{n} flagged")
        except Exception as e:
            logger.warning(f"[POST] Anomaly error (non-fatal): {e}")

    async def _embeddings():
        try:
            from backend.app.services.ai.vector_store import VectorStore
            _t = loop.time()
            await VectorStore.index_case_events(case_id_str, org_id)
            logger.info(f"[POST] ⏱ FAISS:    {loop.time()-_t:.1f}s")
        except Exception as e:
            logger.warning(f"[POST] Embedding error (non-fatal): {e}")

    async def _correlations():
        try:
            from backend.app.services.graph.graph_queries import GraphCorrelationRules
            _t = loop.time()
            corr = await GraphCorrelationRules.run_all_rules(case_id_str, org_id)
            logger.info(f"[POST] ⏱ Correlate:{loop.time()-_t:.1f}s  {corr}")
        except Exception as e:
            logger.warning(f"[POST] Correlation error (non-fatal): {e}")

    await asyncio.gather(_neo4j(), _anomaly(), _embeddings(), _correlations())
    logger.info(f"[POST] 🏁 Post-pipeline done in {loop.time()-_tp:.1f}s")


class ProcessingPipeline:
    """
    Trigger evidence processing as a FastAPI BackgroundTask.
    """

    @staticmethod
    def run_in_background(background_tasks, evidence_id: str, org_id: str, file_bytes: Optional[bytes] = None) -> None:
        try:
            asyncio.create_task(_run_full_pipeline(evidence_id, org_id, file_bytes))
            logger.info(f"[PIPELINE] Scheduled immediate asyncio task for evidence {evidence_id}")
        except Exception:
            background_tasks.add_task(_run_full_pipeline, evidence_id, org_id, file_bytes)
            logger.info(f"[PIPELINE] Scheduled background task for evidence {evidence_id}")

    @staticmethod
    async def trigger_processing(evidence_id: str, org_id: str) -> bool:
        try:
            await EvidenceRepository.update_status(
                evidence_id, org_id, status=EvidenceStatus.QUEUED.value
            )
            asyncio.create_task(_run_full_pipeline(evidence_id, org_id))
            logger.info(f"[PIPELINE] create_task scheduled for {evidence_id}")
            return True
        except Exception as e:
            logger.error(f"[PIPELINE] Trigger failed: {e}")
            await EvidenceRepository.update_status(
                evidence_id, org_id,
                status=EvidenceStatus.FAILED.value,
                error_message=f"Pipeline trigger error: {e}",
            )
            return False
