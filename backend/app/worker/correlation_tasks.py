"""
Correlation Tasks — ForenSight AI
===================================
Celery task that runs the three rule-based Cypher correlation rules
(Architecture Section 5.5.1) against a case's Neo4j graph.

Pipeline position:
  parse → anomaly_detection → embeddings → [THIS] → done

The task is triggered automatically at the end of the embedding task
so the full event set is already in Neo4j with anomaly scores populated.
"""

import logging
import asyncio
from backend.app.worker.celery_app import celery_app
from backend.app.services.graph.graph_queries import GraphCorrelationRules

logger = logging.getLogger(__name__)


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(name="backend.app.worker.correlation_tasks.run_correlation_rules_task")
def run_correlation_rules_task(case_id: str, org_id: str):
    """
    Celery task: execute all three graph correlation rules for a case.

    Rules applied:
      1. PROCESS_INITIATED_CONNECTION — temporal process-to-network binding
      2. REGISTRY_RUN_KEY_PERSISTENCE — Run/RunOnce key detection (T1547.001)
      3. PARENT_OF — parent-child process chain assertion
    """
    logger.info(
        f"Received celery task: run_correlation_rules_task({case_id}, {org_id})"
    )

    async def run():
        return await GraphCorrelationRules.run_all_rules(case_id, org_id)

    results = run_async(run())
    logger.info(f"Correlation rules completed. Results: {results}")

    # Final pipeline step: index case for cross-case similarity
    from backend.app.worker.similarity_tasks import index_case_similarity_task
    index_case_similarity_task.delay(case_id, org_id)

    return {"case_id": case_id, "rules": results}
