"""
ML Tasks — ForenSight AI
Celery task that runs the full multi-model anomaly ensemble
(IsolationForest + HBOS + LOF) and writes results back to MongoDB/Neo4j.
"""

import logging
import asyncio
import numpy as np
from collections import Counter
from bson import ObjectId

from backend.app.worker.celery_app import celery_app
from backend.app.repositories.event_repository import EventRepository
from backend.app.db.mongodb import db_client
from backend.app.db.neo4j import neo4j_client

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {"info": 0.0, "low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(name="backend.app.worker.ml_tasks.run_anomaly_detection_task")
def run_anomaly_detection_task(case_id: str, org_id: str):
    """Run ensemble anomaly detection (IF + HBOS + LOF) for a case."""
    logger.info(f"[ML TASK] run_anomaly_detection_task({case_id}, {org_id})")

    async def run():
        from backend.app.services.intelligence.anomaly.evaluator import ensemble_predict

        events = await EventRepository.list_by_case(case_id, org_id, limit=5000)
        n = len(events)
        if n < 5:
            logger.info(f"[ML TASK] Only {n} events — skipping anomaly detection.")
            return {"status": "skipped", "reason": f"Need ≥5 events, got {n}"}

        # Build feature matrix
        subjects = [e.get("subject", "") for e in events]
        objects  = [e.get("object", "") for e in events]
        actions  = [e.get("action", "") for e in events]
        subj_cnt = Counter(subjects)
        obj_cnt  = Counter(objects)
        act_cnt  = Counter(actions)

        rows = []
        for e in events:
            ts = e.get("timestamp")
            hour      = ts.hour if ts and hasattr(ts, "hour") else 12
            is_wkend  = 1.0 if ts and ts.weekday() >= 5 else 0.0
            subj_freq = subj_cnt[e.get("subject", "")] / n
            obj_freq  = obj_cnt[e.get("object", "")]  / n
            act_freq  = act_cnt[e.get("action", "")]  / n
            sev_val   = SEVERITY_WEIGHTS.get((e.get("severity") or "info").lower(), 0.0)
            rows.append([hour, is_wkend, subj_freq, obj_freq, act_freq, sev_val])

        X = np.array(rows, dtype=float)
        result = ensemble_predict(X)
        flags  = result["flags"]
        scores = result["scores"]

        # Bulk-update MongoDB
        ops = []
        anomaly_count = 0
        for idx, event in enumerate(events):
            is_anom = bool(flags[idx])
            score   = float(scores[idx])
            if is_anom:
                anomaly_count += 1
            ops.append(
                db_client.db["events"].update_one(
                    {"_id": event["_id"]},
                    {"$set": {"is_anomaly": is_anom, "anomaly_score": score}},
                )
            )
        if ops:
            await asyncio.gather(*ops)

        # Sync to Neo4j
        driver = neo4j_client.driver
        if driver:
            batch = [
                {
                    "event_id": str(e["_id"]),
                    "is_anomaly": bool(flags[i]),
                    "anomaly_score": float(scores[i]),
                }
                for i, e in enumerate(events)
            ]
            cypher = """
            UNWIND $batch AS item
            MATCH (s:Entity {case_id:$case_id,organization_id:$org_id})
                  -[r:FORENSIC_ACTION {event_id:item.event_id}]->
                  (o:Entity {case_id:$case_id,organization_id:$org_id})
            SET r.is_anomaly=item.is_anomaly, r.anomaly_score=item.anomaly_score
            """
            try:
                async with driver.session() as session:
                    await session.run(cypher, batch=batch, case_id=case_id, org_id=org_id)
            except Exception as ne:
                logger.error(f"[ML TASK] Neo4j sync failed: {ne}")

        logger.info(f"[ML TASK] Done: {anomaly_count}/{n} anomalies flagged.")
        return {"status": "completed", "total": n, "anomalies": anomaly_count}

    result = run_async(run())

    # Chain to embeddings
    from backend.app.worker.embedding_tasks import generate_event_embeddings_task
    generate_event_embeddings_task.delay(case_id, org_id)

    return result
