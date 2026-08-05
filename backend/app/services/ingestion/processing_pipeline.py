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
import time
import os
import tempfile
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from backend.app.db.mongodb import db_client
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.schemas.evidence import EvidenceStatus

logger = logging.getLogger(__name__)

# Fix scapy Windows cache path before any parser imports scapy
_scapy_cache = os.path.join(tempfile.gettempdir(), "scapy_cache_forensight")
os.makedirs(_scapy_cache, exist_ok=True)
os.environ.setdefault("SCAPY_CACHE_DIR", _scapy_cache)

# Shared thread pool executor capped at 2 workers for low-memory 512MB RAM instances
_parse_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
from backend.app.utils.memory_profiler import log_memory


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

    case_id_str = str(evidence["case_id"])
    filename = evidence.get("filename", evidence_id)
    file_type = evidence.get("file_type", "json")
    logger.info(f"[PIPELINE] ▶ Starting: {filename} ({file_type})")
    await EvidenceRepository.update_status(evidence_id, org_id, EvidenceStatus.PARSING.value)

    loop = asyncio.get_running_loop()
    _t0 = time.perf_counter()
    _t_file_prep_start = _t0  # track file-prep phase start
    file_prep_time = 0.0
    mongo_time = 0.0

    try:
        # ── 2. Obtain file content (use in-memory bytes if available, else download from S3)
        _t_dl = time.perf_counter()
        if file_bytes:
            file_content = file_bytes
            logger.info(f"[PROFILE] File read (in-memory)        0.000s  {len(file_content):,} bytes")
        else:
            if minio_client.client is None:
                connect_to_minio()

            def _download():
                try:
                    resp = minio_client.client.get_object(
                        bucket_name=settings.MINIO_BUCKET_NAME,
                        object_name=evidence["minio_object_name"],
                    )
                    data = resp.read()
                    resp.close()
                    resp.release_conn()
                    return data
                except Exception as err:
                    logger.warning(f"[PIPELINE] S3 download error for {filename}: {err}")
                    return None

            file_content = await loop.run_in_executor(None, _download)
            dl_time = time.perf_counter() - _t_dl
            if not file_content:
                logger.error(f"[PIPELINE] File content unavailable for {filename}. Marking FAILED.")
                await EvidenceRepository.update_status(
                    evidence_id, org_id,
                    status=EvidenceStatus.FAILED.value,
                    error_message="Storage object unavailable. Please click Re-process or re-upload the file.",
                )
                return
            logger.info(f"[PROFILE] File download (S3)           {dl_time:.3f}s  {len(file_content):,} bytes")

        # ── 3. Parse (CPU-bound / blocking I/O → parallel thread executor) ───
        parser = get_parser(file_type)
        file_prep_time = time.perf_counter() - _t_file_prep_start  # everything before parse
        _t_parse = time.perf_counter()
        events = await loop.run_in_executor(
            _parse_executor,
            lambda: parser.parse(file_content, filename=filename),
        )
        parse_seconds = round(time.perf_counter() - _t_parse, 3)

        num_events = len(events)
        total_entities = sum(len(e.get("entities", [])) for e in events)
        total_relationships = sum(len(e.get("relationships", [])) for e in events)

        logger.info(
            f"[PROFILE] Parse ({file_type})               {parse_seconds:.3f}s  "
            f"{num_events} events | {total_entities} entities | {total_relationships} rels"
        )

        if not events:
            if file_type.lower() in ("evtx", "pcap", "sqlite", "csv"):
                raise ValueError(f"0 events returned by parser for {filename}. Parsing failed.")

            events = [{
                "timestamp": datetime.utcnow(),
                "event_type": "generic",
                "source": file_type.lower(),
                "severity": "info",
                "subject": filename,
                "action": "evidence_ingested",
                "object": filename,
                "details": {"file_size": len(file_content), "file_type": file_type},
                "mitre_techniques": []
            }]

        # ── 4. Enrich ─────────────────────────────────────────────────────────
        _t_enrich = time.perf_counter()
        org_oid  = ObjectId(org_id)
        ev_oid   = ObjectId(evidence_id)
        for ev in events:
            ev.update({"case_id": case_id_str, "evidence_id": ev_oid, "organization_id": org_oid,})
        enrich_time = time.perf_counter() - _t_enrich
        logger.info(f"[PROFILE] Event normalization          {enrich_time:.3f}s  ({num_events} events)")

        # ── 5. Check if evidence was deleted during parsing ───────────────────
        still_exists = await EvidenceRepository.get_by_id(evidence_id, org_id)
        if not still_exists:
            logger.warning(f"[PIPELINE] Evidence {evidence_id} was deleted during parsing — aborting DB write.")
            return

        # ── 5a. Purge old derived data for evidence_id before re-processing ─────
        _t_purge = time.perf_counter()
        deleted_count = await EventRepository.delete_by_evidence_id(evidence_id, org_id, filename=filename)
        await GraphRepository.delete_evidence_subgraph(case_id_str, evidence_id)
        purge_time = time.perf_counter() - _t_purge
        if deleted_count > 0:
            logger.info(
                f"[PROFILE] Purge old data               {purge_time:.3f}s  "
                f"({deleted_count} old events deleted for {filename})"
            )

        # ── 5b. MongoDB bulk insert ───────────────────────────────────────────
        _t_mongo = time.perf_counter()
        if events:
            count = await EventRepository.bulk_create(events)
            mongo_time = time.perf_counter() - _t_mongo
            logger.info(f"[PROFILE] MongoDB bulk write           {mongo_time:.3f}s  ({count} inserted)")

        # ── 6. Post-parse enrichment (Neo4j, Anomaly, FAISS, Correlations) ──
        case_id_str = str(evidence["case_id"])
        await EvidenceRepository.update_status(evidence_id, org_id, "analyzing")
        post_time, stage_times = await _run_post_pipeline(events, case_id_str, org_id, loop, parse_seconds)

        # ── 7. Mark PARSED — Complete pipeline finished ─────────────────────
        total_seconds = round(time.perf_counter() - _t0, 3)
        scan_duration_ms = int(total_seconds * 1000)
        await EvidenceRepository.update_status(
            evidence_id, org_id, EvidenceStatus.PARSED.value, scan_duration_ms=scan_duration_ms
        )
        # Mark all events for this evidence as processed (set processed_at timestamp)
        await db_client.db["events"].update_many(
            {"case_id": case_id_str, "$or": [{"evidence_id": ev_oid}, {"evidence_id": str(ev_oid)}]},
            {"$set": {"processed_at": datetime.utcnow()}}
        )

        # Compute "other" time = total − sum of all measured stages
        measured_sum = (
            parse_seconds
            + enrich_time
            + mongo_time
            + stage_times.get("neo4j", 0.0)
            + stage_times.get("ml", 0.0)
            + stage_times.get("faiss", 0.0)
            + stage_times.get("correlations", 0.0)
        )
        other_time = max(0.0, total_seconds - measured_sum)

        logger.info(f"[PIPELINE] 🏁 COMPLETE & PARSED in {total_seconds}s ({scan_duration_ms}ms) — {filename}")
        logger.info(
            f"\n{'='*55}\n"
            f"FORENSIGHT PERFORMANCE REPORT\n"
            f"{'='*55}\n"
            f"Evidence:              {filename}\n"
            f"Events:                {num_events}\n"
            f"{'─'*55}\n"
            f"File preparation:      {file_prep_time:.3f}s\n"
            f"Parse:                 {parse_seconds:.3f}s\n"
            f"Enrich:                {enrich_time:.3f}s\n"
            f"MongoDB insert:        {mongo_time:.3f}s\n"
            f"Neo4j graph sync:      {stage_times.get('neo4j', 0.0):.3f}s\n"
            f"ML anomaly detection:  {stage_times.get('ml', 0.0):.3f}s\n"
            f"FAISS embeddings:      {stage_times.get('faiss', 0.0):.3f}s\n"
            f"Graph correlations:    {stage_times.get('correlations', 0.0):.3f}s\n"
            f"Other (overhead):      {other_time:.3f}s\n"
            f"{'─'*55}\n"
            f"TOTAL:                 {total_seconds:.3f}s\n"
            f"{'='*55}"
        )

    except Exception as e:
        logger.error(f"[PIPELINE] ❌ Failed for {filename}: {e}", exc_info=True)
        total_seconds = round(time.perf_counter() - _t0, 3) if '_t0' in locals() else 0
        scan_duration_ms = int(total_seconds * 1000)
        await EvidenceRepository.update_status(
            evidence_id, org_id,
            status=EvidenceStatus.FAILED.value,
            error_message=str(e)[:500],
            scan_duration_ms=scan_duration_ms,
        )


async def _run_post_pipeline(events, case_id_str: str, org_id: str, loop, parse_seconds: float = 0.0) -> float:
    """
    Post-parse enrichment: Neo4j, anomaly detection, embeddings, correlations.
    All four run concurrently via asyncio.gather.
    Each stage has granular [PROFILE] timing output.
    Returns total post-pipeline wall-clock time in seconds.
    """
    from backend.app.repositories.graph_repository import GraphRepository
    from backend.app.repositories.event_repository import EventRepository

    _tp = time.perf_counter()
    # Stage timers captured via mutable containers so nested async funcs can write to them
    _stage_times: dict = {
        "neo4j": 0.0,
        "ml": 0.0,
        "faiss": 0.0,
        "correlations": 0.0,
    }

    async def _neo4j():
        try:
            _t = time.perf_counter()
            # Log the case_id being written to Neo4j for traceability
            sample_cid = str(events[0].get("case_id", "")) if events else "N/A"
            logger.info(f"[POST] Neo4j sync starting: case_id={sample_cid!r} events={len(events)}")
            synced = await GraphRepository.bulk_import_events(events)
            neo4j_total = time.perf_counter() - _t
            _stage_times["neo4j"] = neo4j_total
            logger.info(
                f"[PROFILE] Neo4j TOTAL                  {neo4j_total:.3f}s  "
                f"({synced} synced, case_id={sample_cid!r})"
            )
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
            _t_fetch = time.perf_counter()
            evs = await EventRepository.list_by_case(case_id_str, org_id, limit=2000)
            fetch_time = time.perf_counter() - _t_fetch
            n = len(evs)
            if n < 1:
                return

            logger.info(f"[PROFILE] ML event fetch               {fetch_time:.3f}s  ({n} events)")

            if n < 5:
                # For small sample sizes (n < 5), flag high/critical severity or tagged events
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
                logger.info(f"[PROFILE] ML (small sample n={n})       — severity-based tagging.")
                return

            # ── Feature extraction ────────────────────────────────────────────
            _t_feat = time.perf_counter()
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
            feat_time = time.perf_counter() - _t_feat
            logger.info(f"[PROFILE] ML feature extraction        {feat_time:.3f}s  ({n} events, {X.shape[1]} features)")

            # ── Ensemble ML ───────────────────────────────────────────────────
            _t_ml = time.perf_counter()
            res = await loop.run_in_executor(None, lambda: ensemble_predict(X))
            flags, scores = res["flags"], res["scores"]
            ml_time = time.perf_counter() - _t_ml
            logger.info(
                f"[PROFILE] ML ensemble                  {ml_time:.3f}s  "
                f"({sum(flags)}/{n} anomalies flagged)"
            )

            # ── MongoDB bulk update ───────────────────────────────────────────
            _t_mongo_update = time.perf_counter()
            bulk_ops = [
                UpdateOne(
                    {"_id": evs[i]["_id"]},
                    {"$set": {"is_anomaly": bool(flags[i]), "anomaly_score": float(scores[i])}},
                )
                for i in range(n)
            ]
            await db_client.db["events"].bulk_write(bulk_ops, ordered=False)
            mongo_update_time = time.perf_counter() - _t_mongo_update
            logger.info(f"[PROFILE] ML MongoDB score update       {mongo_update_time:.3f}s  ({n} events)")

            # ── Neo4j anomaly score sync (batched UNWIND) ─────────────────────
            _t_neo4j_scores = time.perf_counter()
            anomaly_updates = [
                {
                    "event_id": str(evs[i]["_id"]),
                    "is_anomaly": bool(flags[i]),
                    "anomaly_score": float(scores[i]),
                }
                for i in range(n)
            ]
            await GraphRepository.update_anomaly_scores(anomaly_updates)
            neo4j_scores_time = time.perf_counter() - _t_neo4j_scores
            logger.info(f"[PROFILE] ML Neo4j score sync           {neo4j_scores_time:.3f}s  ({n} updates)")

            total_ml_time = feat_time + ml_time + mongo_update_time + neo4j_scores_time
            _stage_times["ml"] = total_ml_time
            logger.info(
                f"[PROFILE] ML TOTAL                     {total_ml_time:.3f}s  "
                f"({sum(flags)}/{n} flagged)"
            )
        except Exception as e:
            logger.warning(f"[POST] Anomaly error (non-fatal): {e}", exc_info=True)

    async def _embeddings():
        try:
            _t = time.perf_counter()
            from backend.app.services.ai.vector_store import VectorStore
            # VectorStore.index_case_events has its own [PROFILE] logging
            await VectorStore.index_case_events(case_id_str, org_id)
            _stage_times["faiss"] = time.perf_counter() - _t
        except Exception as e:
            logger.warning(f"[POST] Embedding error (non-fatal): {e}")

    async def _correlations():
        try:
            from backend.app.services.graph.graph_queries import GraphCorrelationRules
            _t = time.perf_counter()
            corr = await GraphCorrelationRules.run_all_rules(case_id_str, org_id)
            corr_time = time.perf_counter() - _t
            _stage_times["correlations"] = corr_time
            logger.info(
                f"[PROFILE] Graph correlations           {corr_time:.3f}s  "
                f"(total={corr.get('total', 0)}, "
                f"chains={corr.get('process_chains', 0)}, "
                f"paths={corr.get('attack_paths', 0)}, "
                f"cross={corr.get('cross_evidence', 0)})"
            )
        except Exception as e:
            logger.warning(f"[POST] Correlation error (non-fatal): {e}")

    await asyncio.gather(_neo4j(), _anomaly(), _embeddings(), _correlations())
    post_time = time.perf_counter() - _tp
    logger.info(f"[PROFILE] Post-pipeline TOTAL          {post_time:.3f}s")
    return post_time, _stage_times


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
