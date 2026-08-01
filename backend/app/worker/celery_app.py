from celery import Celery
from backend.app.config import settings

# Create Celery instance
celery_app = Celery(
    "forensight_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "backend.app.worker.parser_tasks",
        "backend.app.worker.ml_tasks",
        "backend.app.worker.embedding_tasks",
        "backend.app.worker.report_tasks",
        "backend.app.worker.correlation_tasks",
        "backend.app.worker.similarity_tasks",
        "backend.app.worker.upload_tasks",
    ]
)

# Celery Configurations
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Set prefetch multiplier to 1 to ensure fair task distribution
    worker_prefetch_multiplier=1,
    # Force connection retries on startup
    broker_connection_retry_on_startup=True
)

if __name__ == "__main__":
    celery_app.start()
