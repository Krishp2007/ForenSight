import logging
import asyncio
from backend.app.worker.celery_app import celery_app
from backend.app.services.ml.anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)

def run_async(coro):
    """Run an async coroutine synchronously using the active thread's loop."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@celery_app.task(name="backend.app.worker.ml_tasks.run_anomaly_detection_task")
def run_anomaly_detection_task(case_id: str, org_id: str):
    """Celery background task to calculate anomaly scores and flags across all case events."""
    logger.info(f"Received celery task: run_anomaly_detection_task({case_id}, {org_id})")
    
    async def run():
        # Scoped connection lazy loading handles event-loop binds automatically
        return await AnomalyDetector.detect_and_update_anomalies(case_id, org_id)
        
    result = run_async(run())
    logger.info(f"ML anomaly task completed. Result: {result}")
    
    # Trigger vector embedding generation task for case context
    from backend.app.worker.embedding_tasks import generate_event_embeddings_task
    generate_event_embeddings_task.delay(case_id, org_id)
    
    return result
