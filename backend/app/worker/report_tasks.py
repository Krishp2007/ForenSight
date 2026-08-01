"""
Report Tasks — ForenSight AI
==============================
Celery background task that compiles a full HTML/PDF report for a case,
persists it to MongoDB via ReportRepository, and optionally uploads the
PDF binary to MinIO.

This replaces the previous stub that returned 'pending_implementation'.

Pipeline position (optional — can also be triggered on-demand via API):
  parse → anomaly → embeddings → correlations → [THIS if auto_report=True]
"""

import logging
import asyncio
import io
from datetime import datetime

from backend.app.worker.celery_app import celery_app
from backend.app.services.reports.pdf_compiler import ReportCompiler, weasyprint_available
from backend.app.repositories.report_repository import ReportRepository
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.db.minio import minio_client
from backend.app.config import settings

logger = logging.getLogger(__name__)


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(name="backend.app.worker.report_tasks.generate_pdf_report_task")
def generate_pdf_report_task(case_id: str, org_id: str, triggered_by: str = "system"):
    """
    Celery background task — full report generation pipeline.

    Steps:
      1. Compile HTML report via ReportCompiler (Jinja2 + Copilot AI)
      2. Persist a report metadata document to MongoDB
      3. If WeasyPrint available: compile PDF, upload to MinIO, update report doc
      4. Write audit log entry
    """
    logger.info(f"[REPORT TASK] Starting for case {case_id} org {org_id}")

    async def run():
        # ── Step 1: Compile HTML ──────────────────────────────────────────────
        try:
            html_content = await ReportCompiler.compile_html_report(case_id, org_id)
        except Exception as e:
            logger.error(f"[REPORT TASK] HTML compilation failed: {e}")
            return {"case_id": case_id, "status": "failed", "error": str(e)}

        # ── Step 2: Persist report metadata to MongoDB ────────────────────────
        now = datetime.utcnow()
        report_doc = {
            "case_id": case_id,
            "organization_id": org_id,
            "title": f"Forensic Investigation Report — Case {case_id}",
            "status": "generated",
            "html_length": len(html_content),
            "pdf_minio_path": None,
            "triggered_by": triggered_by,
            "created_at": now,
            "updated_at": now,
        }
        created = await ReportRepository.create(report_doc)
        report_id = created["id"]
        logger.info(f"[REPORT TASK] Report document persisted: {report_id}")

        # ── Step 3: PDF compilation + MinIO upload (if WeasyPrint available) ──
        pdf_path = None
        if weasyprint_available:
            try:
                pdf_bytes = await ReportCompiler.compile_pdf_report(case_id, org_id)
                object_name = f"{org_id}/{case_id}/reports/report_{report_id}.pdf"

                minio_client.client.put_object(
                    bucket_name=settings.MINIO_BUCKET_NAME,
                    object_name=object_name,
                    data=io.BytesIO(pdf_bytes),
                    length=len(pdf_bytes),
                    content_type="application/pdf",
                )
                await ReportRepository.update_pdf_path(report_id, org_id, object_name)
                pdf_path = object_name
                logger.info(f"[REPORT TASK] PDF uploaded to MinIO: {object_name}")
            except Exception as e:
                logger.warning(
                    f"[REPORT TASK] PDF compilation/upload failed (non-fatal): {e}"
                )
        else:
            logger.info(
                "[REPORT TASK] WeasyPrint not available on this host — HTML only."
            )

        # ── Step 4: Audit log ──────────────────────────────────────────────────
        await AuditRepository.log(
            actor_id=triggered_by,
            org_id=org_id,
            action="report.generate",
            entity_type="case",
            entity_id=case_id,
            metadata={
                "report_id": report_id,
                "pdf_path": pdf_path,
                "html_length": len(html_content),
            },
        )

        return {
            "case_id": case_id,
            "report_id": report_id,
            "status": "completed",
            "pdf_path": pdf_path,
        }

    result = run_async(run())
    logger.info(f"[REPORT TASK] Completed: {result}")
    return result
