import hashlib
import io
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from backend.app.schemas.evidence import EvidenceResponse, EvidenceStatus, EvidenceType
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.repositories.case_repository import CaseRepository
from backend.app.db.minio import minio_client
from backend.app.config import settings
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.rbac import require_investigator
from backend.app.schemas.user import UserResponse
from bson import ObjectId

logger = logging.getLogger(__name__)
router = APIRouter(tags=["evidence"])


@router.post("/cases/{case_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_evidence(
    case_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload new digital evidence file (enforces SHA-256 verification and uploads to MinIO)."""
    require_investigator(current_user.role)
    
    # 1. Verify case exists and belongs to organization
    if not ObjectId.is_valid(case_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid case ID format"
        )
        
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or access denied"
        )
        
    # 2. Read file to calculate SHA-256 and size (safely chunked to support large dumps)
    sha256_hash = hashlib.sha256()
    file_bytes = io.BytesIO()
    size_bytes = 0
    
    # Read file chunks
    while True:
        chunk = await file.read(1024 * 1024) # 1MB chunk
        if not chunk:
            break
        sha256_hash.update(chunk)
        file_bytes.write(chunk)
        size_bytes += len(chunk)
        
    sha256 = sha256_hash.hexdigest()
    
    # 3. Check for duplicates in this case
    existing = await EvidenceRepository.get_by_sha256(case_id, sha256)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evidence file with this SHA-256 hash has already been uploaded for this case"
        )
        
    # 4. Upload file payload stream to MinIO
    file_bytes.seek(0)
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
    object_name = f"{current_user.organization_id}/{case_id}/{sha256}.{file_extension}"
    
    try:
        minio_client.client.put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            data=file_bytes,
            length=size_bytes,
            content_type=file.content_type or "application/octet-stream"
        )
        logger.info(f"Successfully uploaded evidence file to MinIO: {object_name}")
    except Exception as e:
        logger.error(f"MinIO storage upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store raw file in MinIO: {e}"
        )
        
    # 5. Insert metadata into MongoDB
    from backend.app.services.ingestion.file_detector import FileDetector
    inferred_type = FileDetector.detect_type(file_bytes.getvalue(), file.filename)
    now = datetime.utcnow()
    evidence_dict = {
        "case_id": ObjectId(case_id),
        "organization_id": ObjectId(current_user.organization_id),
        "filename": file.filename,
        "file_type": inferred_type.value,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "minio_object_name": object_name,
        "status": EvidenceStatus.UPLOADED.value,
        "error_message": None,
        "created_by": ObjectId(current_user.id),
        "created_at": now,
        "updated_at": now
    }
    
    created_evidence = await EvidenceRepository.create(evidence_dict)
    
    # 6. Trigger background processing task
    from backend.app.services.ingestion.processing_pipeline import ProcessingPipeline
    await ProcessingPipeline.trigger_processing(str(created_evidence["_id"]), current_user.organization_id)
    
    # Fetch updated state with queued status
    updated_evidence = await EvidenceRepository.get_by_id(str(created_evidence["_id"]), current_user.organization_id)
    if updated_evidence:
        created_evidence = updated_evidence
        
    # Format MongoDB return values
    created_evidence["id"] = str(created_evidence["_id"])
    created_evidence["case_id"] = str(created_evidence["case_id"])
    created_evidence["organization_id"] = str(created_evidence["organization_id"])
    created_evidence["created_by"] = str(created_evidence["created_by"])
    return created_evidence

@router.get("/cases/{case_id}/evidence", response_model=List[EvidenceResponse])
async def list_case_evidence(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve metadata of all files uploaded to a specific case."""
    if not ObjectId.is_valid(case_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid case ID format"
        )
        
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or access denied"
        )
        
    evidence_list = await EvidenceRepository.list_by_case(case_id, current_user.organization_id)
    response_list = []
    for e in evidence_list:
        e["id"] = str(e["_id"])
        e["case_id"] = str(e["case_id"])
        e["organization_id"] = str(e["organization_id"])
        e["created_by"] = str(e["created_by"])
        response_list.append(e)
    return response_list

@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence_details(
    evidence_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Fetch status or processing errors of a specific uploaded evidence."""
    if not ObjectId.is_valid(evidence_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid evidence ID format"
        )
        
    evidence = await EvidenceRepository.get_by_id(evidence_id, current_user.organization_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found or access denied"
        )
        
    evidence["id"] = str(evidence["_id"])
    evidence["case_id"] = str(evidence["case_id"])
    evidence["organization_id"] = str(evidence["organization_id"])
    evidence["created_by"] = str(evidence["created_by"])
    return evidence
