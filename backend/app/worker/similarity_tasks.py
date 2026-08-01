"""
Similarity Tasks — ForenSight AI
====================================
Celery task that indexes a completed case into Qdrant for cross-case
similarity search (Architecture Section 5.5.3).

Pipeline position (final step):
  parse → anomaly → embeddings → correlations → [THIS]
"""

import logging
import asyncio
from backend.app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(name="backend.app.worker.similarity_tasks.index_case_similarity_task")
def index_case_similarity_task(case_id: str, org_id: str):
    """Index the case into Qdrant for cross-case similarity search."""
    logger.info(f"[SIM TASK] Indexing case {case_id} into Qdrant")

    async def run():
        from backend.app.services.intelligence.similarity_service import (
            index_case_for_similarity,
        )
        return await index_case_for_similarity(case_id, org_id)

    result = run_async(run())
    logger.info(f"[SIM TASK] Done: {result}")
    return {"case_id": case_id, "indexed": result}
