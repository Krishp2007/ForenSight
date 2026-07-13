import logging
from backend.app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="backend.app.worker.embedding_tasks.generate_event_embeddings_task")
def generate_event_embeddings_task(case_id: str, org_id: str):
    """Placeholder Celery task for generating sentence embeddings and loading into FAISS."""
    logger.info(f"Generating event embeddings for case: {case_id} org: {org_id}")
    return {"case_id": case_id, "status": "pending_implementation"}
