import hashlib
import io
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from backend.app.schemas.evidence import EvidenceResponse, EvidenceStatus
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


# ── Upload ─────────────────────────────────────────────────────────────────────

@router.post("/cases/{case_id}/evidence", response_model=EvidenceResponse,
             status_code=status.HTTP_202_ACCEPTED)
async def upload_evidence(
    case_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
):
    """Upload a new digital evidence file; SHA-256 hashed, stored in MinIO, then processed."""
    require_investigator(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

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

    existing = await EvidenceRepository.get_by_sha256(case_id, sha256)
    if existing:
        raise HTTPException(status_code=409, detail="File with this SHA-256 already uploaded")

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin"
    object_name = f"{current_user.organization_id}/{case_id}/{sha256}.{ext}"
    buf.seek(0)
    try:
        minio_client.client.put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            data=buf, length=size_bytes,
            content_type=file.content_type or "application/octet-stream",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MinIO upload failed: {e}")

    from backend.app.services.ingestion.file_detector import FileDetector
    inferred_type = FileDetector.detect_type(buf.getvalue(), file.filename)
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
        "updated_at": now,
    }
    created = await EvidenceRepository.create(evidence_dict)

    from backend.app.services.ingestion.processing_pipeline import ProcessingPipeline
    ProcessingPipeline.run_in_background(background_tasks, str(created["_id"]),
                                         current_user.organization_id)

    updated = await EvidenceRepository.get_by_id(str(created["_id"]), current_user.organization_id)
    if updated:
        created = updated
    created["id"] = str(created["_id"])
    created["case_id"] = str(created["case_id"])
    created["organization_id"] = str(created["organization_id"])
    created["created_by"] = str(created["created_by"])

    await AuditRepository.log(
        actor_id=current_user.id, org_id=current_user.organization_id,
        action="evidence.upload", entity_type="evidence", entity_id=created["id"],
        metadata={"filename": file.filename, "sha256": sha256,
                  "size_bytes": size_bytes, "file_type": inferred_type.value,
                  "case_id": case_id},
    )
    return created


# ── Re-process ─────────────────────────────────────────────────────────────────

@router.post("/cases/{case_id}/evidence/{evidence_id}/reprocess",
             status_code=status.HTTP_202_ACCEPTED)
async def reprocess_evidence(
    case_id: str, evidence_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
):
    """Re-run the full pipeline: parse → Neo4j → anomalies → embeddings → correlations."""
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
    ProcessingPipeline.run_in_background(background_tasks, evidence_id,
                                         current_user.organization_id)
    await AuditRepository.log(
        actor_id=current_user.id, org_id=current_user.organization_id,
        action="evidence.reprocess", entity_type="evidence", entity_id=evidence_id,
        metadata={"filename": evidence.get("filename"), "case_id": case_id},
    )
    return {"detail": "Re-processing started", "evidence_id": evidence_id}


# ── Delete ─────────────────────────────────────────────────────────────────────

@router.delete("/cases/{case_id}/evidence/{evidence_id}",
               status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(
    case_id: str, evidence_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Delete evidence — cascades to MinIO file, MongoDB events, and Neo4j graph edges."""
    require_investigator(current_user.role)
    if not ObjectId.is_valid(case_id) or not ObjectId.is_valid(evidence_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")
    evidence = await EvidenceRepository.get_by_id(evidence_id, current_user.organization_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    # 1. MinIO
    try:
        minio_client.client.remove_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=evidence["minio_object_name"],
        )
    except Exception as e:
        logger.warning(f"MinIO delete skipped: {e}")

    # 2. MongoDB events
    from backend.app.db.mongodb import db_client as mongo
    res = await mongo.db["events"].delete_many({
        "evidence_id": ObjectId(evidence_id),
        "organization_id": ObjectId(current_user.organization_id),
    })
    logger.info(f"Deleted {res.deleted_count} events for evidence {evidence_id}")

    # 3. Neo4j edges + orphan nodes
    try:
        from backend.app.db.neo4j import neo4j_client
        if neo4j_client.driver:
            async with neo4j_client.driver.session() as sess:
                await sess.run(
                    "MATCH ()-[r:FORENSIC_ACTION {evidence_id:$eid, case_id:$cid, organization_id:$oid}]->() DELETE r",
                    eid=evidence_id, cid=case_id, oid=current_user.organization_id,
                )
                await sess.run(
                    """MATCH (n:Entity {case_id:$cid, organization_id:$oid})
                       WHERE NOT (n)-[:FORENSIC_ACTION]-() AND NOT ()-[:FORENSIC_ACTION]->(n)
                       DELETE n""",
                    cid=case_id, oid=current_user.organization_id,
                )
    except Exception as e:
        logger.warning(f"Neo4j cleanup skipped: {e}")

    # 4. MongoDB evidence doc
    await EvidenceRepository.delete(evidence_id, current_user.organization_id)

    await AuditRepository.log(
        actor_id=current_user.id, org_id=current_user.organization_id,
        action="evidence.delete", entity_type="evidence", entity_id=evidence_id,
        metadata={"filename": evidence.get("filename"), "case_id": case_id},
    )
    return None


# ── Per-evidence graph ──────────────────────────────────────────────────────────

@router.get("/cases/{case_id}/evidence/{evidence_id}/graph")
async def get_evidence_graph(
    case_id: str, evidence_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Graph (nodes + edges) produced specifically by one evidence file."""
    if not ObjectId.is_valid(case_id) or not ObjectId.is_valid(evidence_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    from backend.app.db.neo4j import neo4j_client
    if not neo4j_client.driver:
        return {"nodes": [], "edges": []}

    cypher = """
    MATCH (s:Entity {case_id:$cid, organization_id:$oid})
          -[r:FORENSIC_ACTION {case_id:$cid, organization_id:$oid, evidence_id:$eid}]->
          (o:Entity {case_id:$cid, organization_id:$oid})
    RETURN s.name AS sn, s.type AS st, o.name AS tn, o.type AS tt,
           r.action AS action, r.severity AS severity,
           r.is_anomaly AS is_anomaly
    LIMIT 1000
    """
    nodes_dict, edges = {}, []
    try:
        async with neo4j_client.driver.session() as sess:
            result = await sess.run(cypher, cid=case_id,
                                    oid=current_user.organization_id, eid=evidence_id)
            for rec in await result.data():
                for name, ntype in [(rec["sn"], rec["st"]), (rec["tn"], rec["tt"])]:
                    if name not in nodes_dict:
                        nodes_dict[name] = {"id": name, "label": name, "type": ntype}
                edges.append({"source": rec["sn"], "target": rec["tn"],
                               "action": rec["action"], "severity": rec["severity"],
                               "is_anomaly": rec.get("is_anomaly", False)})
    except Exception as e:
        logger.error(f"Per-evidence graph: {e}")

    return {"nodes": list(nodes_dict.values()), "edges": edges}


# ── Per-evidence report ─────────────────────────────────────────────────────────

@router.get("/cases/{case_id}/evidence/{evidence_id}/report/html",
            response_class=HTMLResponse)
async def get_evidence_report(
    case_id: str, evidence_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """HTML report scoped to a single evidence file."""
    if not ObjectId.is_valid(case_id) or not ObjectId.is_valid(evidence_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")
    evidence = await EvidenceRepository.get_by_id(evidence_id, current_user.organization_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    from backend.app.db.mongodb import db_client as mongo
    from backend.app.services.reports.pdf_compiler import ReportCompiler
    from backend.app.services.context.report_context import build_report_context

    context = await build_report_context(case_id, current_user.organization_id)
    ev_oid  = ObjectId(evidence_id)
    org_oid = ObjectId(current_user.organization_id)

    context["total_events"] = await mongo.db["events"].count_documents(
        {"evidence_id": ev_oid, "organization_id": org_oid})
    context["anomalies_count"] = await mongo.db["events"].count_documents(
        {"evidence_id": ev_oid, "organization_id": org_oid, "is_anomaly": True})
    context["critical_high_count"] = await mongo.db["events"].count_documents(
        {"evidence_id": ev_oid, "organization_id": org_oid,
         "severity": {"$in": ["critical", "high"]}})
    context["copilot_analysis_html"] = (
        f"<h3>Evidence Report: {evidence.get('filename')}</h3>"
        f"<p>Scoped to <strong>{evidence.get('filename')}</strong> "
        f"({evidence.get('file_type','').upper()}) — "
        f"<strong>{context['total_events']:,}</strong> events, "
        f"<strong>{context['anomalies_count']}</strong> anomalies, "
        f"<strong>{context['critical_high_count']}</strong> critical/high.</p>"
    )
    context["case"] = dict(context["case"])
    context["case"]["title"] = f"{context['case'].get('title')} — {evidence.get('filename')}"

    if not context.get("copilot_analysis_html"):
        context["copilot_analysis_html"] = ReportCompiler._build_fallback_analysis_html(context)

    return HTMLResponse(content=ReportCompiler._render_template(context))


# ── SSE stream ──────────────────────────────────────────────────────────────────

@router.get("/cases/{case_id}/evidence/{evidence_id}/stream")
async def stream_evidence_status(
    case_id: str, evidence_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Real-time Server-Sent Events stream for processing status."""
    if not ObjectId.is_valid(case_id) or not ObjectId.is_valid(evidence_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")
    from backend.app.pipeline.event_stream import EventStream
    return StreamingResponse(
        EventStream.subscribe(evidence_id), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── List ────────────────────────────────────────────────────────────────────────

@router.get("/cases/{case_id}/evidence", response_model=List[EvidenceResponse])
async def list_case_evidence(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")
    evidence_list = await EvidenceRepository.list_by_case(case_id, current_user.organization_id)
    for e in evidence_list:
        e["id"] = str(e["_id"])
        e["case_id"] = str(e["case_id"])
        e["organization_id"] = str(e["organization_id"])
        e["created_by"] = str(e["created_by"])
    return evidence_list


# ── Get single ──────────────────────────────────────────────────────────────────

@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence_details(
    evidence_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    if not ObjectId.is_valid(evidence_id):
        raise HTTPException(status_code=400, detail="Invalid evidence ID format")
    evidence = await EvidenceRepository.get_by_id(evidence_id, current_user.organization_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found or access denied")
    evidence["id"] = str(evidence["_id"])
    evidence["case_id"] = str(evidence["case_id"])
    evidence["organization_id"] = str(evidence["organization_id"])
    evidence["created_by"] = str(evidence["created_by"])
    return evidence
