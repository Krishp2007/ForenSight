import logging
import asyncio
from backend.app.worker.celery_app import celery_app
from backend.app.services.ai.vector_store import VectorStore

logger = logging.getLogger(__name__)

def run_async(coro):
    """Run an async coroutine synchronously using the active thread's loop."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@celery_app.task(name="backend.app.worker.embedding_tasks.generate_event_embeddings_task")
def generate_event_embeddings_task(case_id: str, org_id: str):
    """Celery background task to calculate sentence embeddings and save to FAISS index."""
    logger.info(f"Received celery task: generate_event_embeddings_task({case_id}, {org_id})")
    
    async def run():
        return await VectorStore.index_case_events(case_id, org_id)
        
    result = run_async(run())
    logger.info(f"Vector embedding indexing completed. Status: {result}")

    # Trigger graph correlation rules — runs after embeddings so the full
    # event set is in Neo4j and anomaly scores are populated
    from backend.app.worker.correlation_tasks import run_correlation_rules_task
    run_correlation_rules_task.delay(case_id, org_id)

    return {"case_id": case_id, "indexed": result}
