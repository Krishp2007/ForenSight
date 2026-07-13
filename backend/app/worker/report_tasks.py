import logging
from backend.app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="backend.app.worker.report_tasks.generate_pdf_report_task")
def generate_pdf_report_task(case_id: str, org_id: str):
    """Placeholder Celery task for compiling the PDF investigation report."""
    logger.info(f"Generating PDF report for case: {case_id} org: {org_id}")
    return {"case_id": case_id, "status": "pending_implementation"}
