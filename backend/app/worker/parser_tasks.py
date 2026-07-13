import asyncio
import logging
from bson import ObjectId
from celery.utils.log import get_task_logger

from backend.app.worker.celery_app import celery_app
from backend.app.db.mongodb import db_client, connect_to_mongo
from backend.app.db.minio import minio_client
from backend.app.config import settings
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.repositories.event_repository import EventRepository
from backend.app.parsers import get_parser
from backend.app.schemas.evidence import EvidenceStatus

# Celery task logger
logger = get_task_logger(__name__)

def run_async(coro):
    """Run an async coroutine synchronously using the loop context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

async def _process_evidence_async(evidence_id: str, org_id: str):
    """Async database and MinIO helper to process evidence."""
    # 1. Force reconnect MongoDB client to bind to the active thread's loop context
    if db_client.client:
        try:
            db_client.client.close()
        except Exception:
            pass
            
    from motor.motor_asyncio import AsyncIOMotorClient
    db_client.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db_client.db = db_client.client[settings.MONGODB_DB_NAME]

    # 2. Fetch Evidence Metadata
    evidence = await EvidenceRepository.get_by_id(evidence_id, org_id)
    if not evidence:
        logger.error(f"Evidence {evidence_id} not found in org {org_id}. Aborting task.")
        return
        
    # Update status to parsing
    await EvidenceRepository.update_status(evidence_id, org_id, EvidenceStatus.PARSING.value)
    logger.info(f"Start parsing evidence {evidence_id} ({evidence['filename']})")
    
    try:
        # 3. Retrieve raw binary file from MinIO object store
        response = minio_client.client.get_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=evidence["minio_object_name"]
        )
        file_content = response.read()
        response.close()
        response.release_conn()
        
        # 4. Parse events using appropriate parser based on file type
        parser = get_parser(evidence["file_type"])
        logger.info(f"Resolved parser class: {parser.__class__.__name__}")
        
        parsed_events = parser.parse(file_content, filename=evidence["filename"])
        logger.info(f"Parsed {len(parsed_events)} raw events from file.")
        
        # 5. Enrich events with parent case, organization, and evidence metadata references
        enriched_events = []
        for event in parsed_events:
            event.update({
                "case_id": ObjectId(evidence["case_id"]),
                "evidence_id": ObjectId(evidence_id),
                "organization_id": ObjectId(org_id)
            })
            enriched_events.append(event)
            
        # 6. Bulk insert events into MongoDB
        inserted_count = 0
        if enriched_events:
            inserted_count = await EventRepository.bulk_create(enriched_events)
            
        logger.info(f"Successfully bulk inserted {inserted_count} events into MongoDB.")
        
        # Update evidence status to parsed
        await EvidenceRepository.update_status(evidence_id, org_id, EvidenceStatus.PARSED.value)
        
    except Exception as e:
        logger.error(f"Error parsing evidence {evidence_id}: {e}")
        # Update status to failed
        await EvidenceRepository.update_status(
            evidence_id, org_id, 
            status=EvidenceStatus.FAILED.value, 
            error_message=str(e)
        )

@celery_app.task(name="backend.app.worker.parser_tasks.process_evidence_task")
def process_evidence_task(evidence_id: str, org_id: str):
    """Celery background task wrapper for processing forensic evidence files."""
    logger.info(f"Received celery task: process_evidence_task({evidence_id}, {org_id})")
    run_async(_process_evidence_async(evidence_id, org_id))
    return {"evidence_id": evidence_id, "status": "completed"}
