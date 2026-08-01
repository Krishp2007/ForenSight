import hashlib
import io
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from backend.app.schemas.evidence import EvidenceResponse, EvidenceStatus, EvidenceType
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.repositories.case_repository import CaseRepository
from backend.app.db.minio import minio_client
from backend.app.config import settings
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.rbac import require_investigator
from backend.app.schemas.user import UserResponse
from backend.app.repositories.audit_repository import AuditRepository
from bson import ObjectId

logger = logging.getLogger(__name__)
router = APIRouter(tags=["evidence"])


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post("/cases/{case_id}/evidence", response_model=EvidenceResponse,
             status_code=status.HTTP_202_ACCEPTED)
async def upload_evidence(
    case_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
):
    """Upload a new digital evidence file; SHA-256 hashed and stored in MinIO."""
    require_investigator(current_user.role)

    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")

    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    # Read + hash in 1 MB chunks
    sha256_hash = hashlib.sha256()
    buf = io.BytesIO()
    size_bytes = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        sha256_hash.update(chunk)
        buf.write(chunk)
        size_bytes += len(chunk)
    sha256 = sha256_hash.hexdigest()

    # Duplicate check
    existing = await EvidenceRepository.get_by_sha256(case_id, sha256)
    if existing:
        raise HTTPException(status_code=409,
                            detail="File with this SHA-256 already uploaded for this case")

    # MinIO upload
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin"
    object_name = f"{current_user.organization_id}/{case_id}/{sha256}.{ext}"
    buf.seek(0)
    try:
        minio_client.client.put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            data=buf,
            length=size_bytes,
            content_type=file.content_type or "application/octet-stream",
        )
    except Exception as e:
        logger.error(f"MinIO upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store file: {e}")

    # Detect file type
    from backend.app.services.ingestion.file_detector import FileDetector
    inferred_type = FileDetector.detect_type(buf.getvalue(), file.filename)

    now = datetime.utcnow()
    evidence_dict = {
        "case_id":           ObjectId(case_id),
        "organization_id":   ObjectId(current_user.organization_id),
        "filename":          file.filename,
        "file_type":         inferred_type.value,
        "size_bytes":        size_bytes,
        "sha256":            sha256,
        "minio_object_name": object_name,
        "status":            EvidenceStatus.UPLOADED.value,
        "error_message":     None,
        "created_by":        ObjectId(current_user.id),
        "created_at":        now,
        "updated_at":        now,
    }
    created = await EvidenceRepository.create(evidence_dict)

    # Trigger processing pipeline
    from backend.app.services.ingestion.processing_pipeline import ProcessingPipeline
    await ProcessingPipeline.trigger_processing(str(created["_id"]),
                                                current_user.organization_id)

    updated = await EvidenceRepository.get_by_id(str(created["_id"]),
                                                  current_user.organization_id)
    if updated:
        created = updated

    created["id"]              = str(created["_id"])
    created["case_id"]         = str(created["case_id"])
    created["organization_id"] = str(created["organization_id"])
    created["created_by"]      = str(created["created_by"])

    await AuditRepository.log(
        actor_id=current_user.id,
        org_id=current_user.organization_id,
        action="evidence.upload",
        entity_type="evidence",
        entity_id=created["id"],
        metadata={"filename": file.filename, "sha256": sha256,
                  "size_bytes": size_bytes, "file_type": inferred_type.value,
                  "case_id": case_id},
    )
    return created


# ── Re-process ────────────────────────────────────────────────────────────────

@router.post("/cases/{case_id}/evidence/{evidence_id}/reprocess",
             status_code=status.HTTP_202_ACCEPTED)
async def reprocess_evidence(
    case_id: str,
    evidence_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Re-trigger the full pipeline for already-uploaded evidence.
    Re-syncs Neo4j, re-runs anomaly detection, rebuilds embeddings and correlations."""
    require_investigator(current_user.role)

    if not ObjectId.is_valid(case_id) or not ObjectId.is_valid(evidence_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    evidence = await EvidenceRepository.get_by_id(evidence_id, current_user.organization_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    await EvidenceRepository.update_status(evidence_id, current_user.organization_id,
                                           EvidenceStatus.UPLOADED.value)

    from backend.app.services.ingestion.processing_pipeline import ProcessingPipeline
    await ProcessingPipeline.trigger_processing(evidence_id, current_user.organization_id)

    await AuditRepository.log(
        actor_id=current_user.id,
        org_id=current_user.organization_id,
        action="evidence.reprocess",
        entity_type="evidence",
        entity_id=evidence_id,
        metadata={"filename": evidence.get("filename"), "case_id": case_id},
    )
    return {"detail": "Re-processing started", "evidence_id": evidence_id}


# ── SSE stream ────────────────────────────────────────────────────────────────

@router.get("/cases/{case_id}/evidence/{evidence_id}/stream")
async def stream_evidence_status(
    case_id: str,
    evidence_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Stream real-time processing status updates via Server-Sent Events."""
    if not ObjectId.is_valid(case_id) or not ObjectId.is_valid(evidence_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    from backend.app.pipeline.event_stream import EventStream
    return StreamingResponse(
        EventStream.subscribe(evidence_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/cases/{case_id}/evidence", response_model=List[EvidenceResponse])
async def list_case_evidence(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Retrieve metadata of all evidence files uploaded to a case."""
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")

    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    evidence_list = await EvidenceRepository.list_by_case(case_id, current_user.organization_id)
    for e in evidence_list:
        e["id"]              = str(e["_id"])
        e["case_id"]         = str(e["case_id"])
        e["organization_id"] = str(e["organization_id"])
        e["created_by"]      = str(e["created_by"])
    return evidence_list


# ── Get single ────────────────────────────────────────────────────────────────

@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence_details(
    evidence_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Fetch status and processing details for a specific evidence file."""
    if not ObjectId.is_valid(evidence_id):
        raise HTTPException(status_code=400, detail="Invalid evidence ID format")

    evidence = await EvidenceRepository.get_by_id(evidence_id, current_user.organization_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found or access denied")

    evidence["id"]              = str(evidence["_id"])
    evidence["case_id"]         = str(evidence["case_id"])
    evidence["organization_id"] = str(evidence["organization_id"])
    evidence["created_by"]      = str(evidence["created_by"])
    return evidence
