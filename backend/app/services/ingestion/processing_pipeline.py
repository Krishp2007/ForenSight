import logging
from backend.app.worker.parser_tasks import process_evidence_task
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.schemas.evidence import EvidenceStatus

logger = logging.getLogger(__name__)

class ProcessingPipeline:
    @staticmethod
    async def trigger_processing(evidence_id: str, org_id: str) -> bool:
        """Queue evidence for background parsing and transition state to queued."""
        try:
            # 1. Update status in MongoDB to queued
            await EvidenceRepository.update_status(
                evidence_id, 
                org_id, 
                status=EvidenceStatus.QUEUED.value
            )
            
            # 2. Dispatch Celery task
            task = process_evidence_task.delay(evidence_id, org_id)
            logger.info(f"Successfully dispatched process_evidence_task for evidence {evidence_id}. Task ID: {task.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to dispatch processing task: {e}")
            # Revert status to uploaded / failed
            await EvidenceRepository.update_status(
                evidence_id, 
                org_id, 
                status=EvidenceStatus.FAILED.value, 
                error_message=f"Queue dispatch failure: {e}"
            )
            return False
