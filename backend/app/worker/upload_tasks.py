"""
Upload Tasks — ForenSight AI
==============================
Celery task for post-upload processing that runs in the background.
This decouples large-file hashing / type detection from the HTTP request
lifecycle so the API returns immediately after writing to MinIO.

Currently invoked at the end of the evidence upload API route to trigger
the full pipeline: detect type → update metadata → queue parsing.
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


@celery_app.task(name="backend.app.worker.upload_tasks.post_upload_task")
def post_upload_task(evidence_id: str, org_id: str):
    """
    Background task triggered after evidence is written to MinIO.

    Steps:
      1. Verify evidence record exists in MongoDB
      2. Detect file type from MinIO object (magic bytes)
      3. Update evidence metadata if type changed
      4. Queue the parser task

    This keeps the upload API response under 500ms even for large files.
    """
    logger.info(f"[UPLOAD TASK] post_upload_task({evidence_id}, {org_id})")

    async def run():
        from backend.app.repositories.evidence_repository import EvidenceRepository
        from backend.app.schemas.evidence import EvidenceStatus
        from backend.app.db.minio import minio_client
        from backend.app.config import settings
        from backend.app.services.ingestion.file_detector import FileDetector

        evidence = await EvidenceRepository.get_by_id(evidence_id, org_id)
        if not evidence:
            logger.error(f"[UPLOAD TASK] Evidence {evidence_id} not found. Aborting.")
            return {"status": "error", "reason": "evidence_not_found"}

        # Re-detect type from raw bytes (supports the case where detection
        # at upload time was ambiguous due to missing content-type header)
        try:
            response = minio_client.client.get_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=evidence["minio_object_name"],
            )
            # Read only the first 512 bytes for magic detection
            header = response.read(512)
            response.close()
            response.release_conn()

            detected_type = FileDetector.detect_type(header, evidence["filename"])
            if detected_type.value != evidence.get("file_type"):
                # Update the corrected type in MongoDB
                from backend.app.db.mongodb import db_client
                from bson import ObjectId
                await db_client.db["evidence"].update_one(
                    {"_id": ObjectId(evidence_id)},
                    {"$set": {"file_type": detected_type.value}},
                )
                logger.info(
                    f"[UPLOAD TASK] Type corrected: "
                    f"{evidence.get('file_type')} → {detected_type.value}"
                )
        except Exception as e:
            logger.warning(f"[UPLOAD TASK] Type re-detection failed (non-fatal): {e}")

        # Queue the full parsing pipeline
        from backend.app.worker.parser_tasks import process_evidence_task
        process_evidence_task.delay(evidence_id, org_id)

        return {"status": "queued", "evidence_id": evidence_id}

    result = run_async(run())
    logger.info(f"[UPLOAD TASK] Done: {result}")
    return result
