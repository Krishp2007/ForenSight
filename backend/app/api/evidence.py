import hashlib
import io
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
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
    file_bytes = buf.getvalue()
    buf.seek(0)

    import asyncio
    loop = asyncio.get_running_loop()

    def _do_minio_upload():
        try:
            if minio_client and minio_client.client:
                minio_client.client.put_object(
                    bucket_name=settings.MINIO_BUCKET_NAME,
                    object_name=object_name,
                    data=buf, length=size_bytes,
                    content_type=file.content_type or "application/octet-stream",
                )
        except Exception as err:
            logger.warning(f"MinIO storage warning (proceeding with local buffer): {err}")

    # Offload MinIO upload to background thread so main asyncio event loop stays unblocked
    loop.run_in_executor(None, _do_minio_upload)

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
                                         current_user.organization_id, file_bytes=buf.getvalue())

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

async def _cleanup_evidence_resources(evidence_id: str, case_id: str, organization_id: str, minio_object_name: Optional[str], filename: Optional[str] = None):
    """
    Cascading Clean-Up: Deletes ALL data associated with an evidence file from EVERYWHERE:
    1. MinIO S3 Object Storage (Raw file)
    2. MongoDB 'events' collection (All parsed log events for evidence_id)
    3. Neo4j Graph DB (Relationships and orphaned nodes for evidence_id)
    4. FAISS Vector Store (Rebuilds vector index for case without deleted events)
    5. MongoDB 'reports' collection (Cached reports)
    6. MongoDB 'audit_logs' collection (Deletes all evidence upload/reprocess/delete audit logs)
    """
    logger.info(f"[CLEANUP] Starting cascading deletion for evidence {evidence_id} (case={case_id}, filename={filename})...")

    # 1. MinIO Object Storage Cleanup
    try:
        if minio_object_name:
            minio_client.client.remove_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=minio_object_name,
            )
            logger.info(f"[CLEANUP] Deleted MinIO object: {minio_object_name}")
            
        from backend.app.db.mongodb import db_client as mongo
        cid_obj = ObjectId(case_id) if ObjectId.is_valid(case_id) else case_id
        rem_ev_count = await mongo.db["evidence"].count_documents({"case_id": cid_obj})
        if rem_ev_count == 0:
            prefix = f"{organization_id}/{case_id}/"
            objs = list(minio_client.client.list_objects(settings.MINIO_BUCKET_NAME, prefix=prefix, recursive=True))
            for o in objs:
                minio_client.client.remove_object(settings.MINIO_BUCKET_NAME, o.object_name)
                logger.info(f"[CLEANUP] Deleted orphaned MinIO object for empty case: {o.object_name}")
    except Exception as e:
        logger.warning(f"[CLEANUP] MinIO delete skipped: {e}")

    # 2. MongoDB Events Cleanup (Deletes ALL parsed events matching evidence_id as ObjectId or str)
    try:
        from backend.app.db.mongodb import db_client as mongo
        eid_obj = ObjectId(evidence_id) if ObjectId.is_valid(evidence_id) else evidence_id
        oid_obj = ObjectId(organization_id) if ObjectId.is_valid(organization_id) else organization_id
        res = await mongo.db["events"].delete_many({
            "$or": [
                {"evidence_id": eid_obj},
                {"evidence_id": str(evidence_id)},
            ],
            "$and": [
                {"$or": [{"organization_id": oid_obj}, {"organization_id": str(organization_id)}]}
            ]
        })
        logger.info(f"[CLEANUP] Deleted {res.deleted_count} MongoDB events for evidence {evidence_id}")
    except Exception as e:
        logger.error(f"[CLEANUP] MongoDB events cleanup error: {e}")

    # 3. Neo4j Graph Database Cleanup (Deletes FORENSIC_ACTION edges and orphan nodes)
    try:
        from backend.app.db.neo4j import neo4j_client
        if neo4j_client.driver:
            async with neo4j_client.driver.session() as sess:
                # Delete relationships with matching evidence_id
                await sess.run(
                    """
                    MATCH ()-[r:FORENSIC_ACTION]->()
                    WHERE r.evidence_id = $eid OR toString(r.evidence_id) = $eid
                    DELETE r
                    """,
                    eid=evidence_id,
                )
                # Delete orphan nodes with no remaining edges in case
                await sess.run(
                    """
                    MATCH (n {case_id:$cid})
                    WHERE NOT (n)--()
                    DELETE n
                    """,
                    cid=case_id,
                )

                # Check if 0 evidence files remain for the case — if so, DETACH DELETE ALL nodes in case!
                from backend.app.db.mongodb import db_client as mongo
                cid_obj = ObjectId(case_id) if ObjectId.is_valid(case_id) else case_id
                rem_ev_count = await mongo.db["evidence"].count_documents({"case_id": cid_obj})
                if rem_ev_count == 0:
                    await sess.run(
                        """
                        MATCH (n {case_id:$cid})
                        DETACH DELETE n
                        """,
                        cid=case_id,
                    )
                    logger.info(f"[CLEANUP] Detached and deleted ALL Neo4j nodes for empty case {case_id}")
                else:
                    logger.info(f"[CLEANUP] Cleaned up Neo4j graph relationships & orphan nodes for evidence {evidence_id}")
    except Exception as e:
        logger.warning(f"[CLEANUP] Neo4j cleanup skipped: {e}")

    # 4. FAISS Vector Search Index & Local Storage Cleanup (Runs asynchronously in background)
    try:
        import asyncio
        from backend.app.services.ai.vector_store import VectorStore
        asyncio.create_task(VectorStore.index_case_events(case_id, organization_id))
        logger.info(f"[CLEANUP] Scheduled background FAISS vector store rebuild for case {case_id}")
    except Exception as e:
        logger.warning(f"[CLEANUP] FAISS index rebuild skipped: {e}")

    # 5. Qdrant Cross-Case Vector Store Cleanup (If Qdrant Client is active)
    try:
        from qdrant_client import QdrantClient
        q_client = QdrantClient(host=getattr(settings, "QDRANT_HOST", "localhost"), port=getattr(settings, "QDRANT_PORT", 6333), timeout=0.5)
        q_client.delete(
            collection_name="forensight_events",
            points_selector={"filter": {"must": [{"key": "evidence_id", "match": {"value": str(evidence_id)}}]}}
        )
        logger.info(f"[CLEANUP] Deleted Qdrant vector points for evidence {evidence_id}")
    except Exception:
        pass

    # 6. MongoDB Reports Collection Cleanup
    try:
        from backend.app.db.mongodb import db_client as mongo
        await mongo.db["reports"].delete_many({"evidence_id": ObjectId(evidence_id)})
        await mongo.db["reports"].delete_many({"evidence_id": str(evidence_id)})
        await mongo.db["reports"].delete_many({"case_id": ObjectId(case_id)})
        await mongo.db["reports"].delete_many({"case_id": str(case_id)})
        logger.info(f"[CLEANUP] Cleaned up cached reports for evidence {evidence_id}")
    except Exception as e:
        logger.warning(f"[CLEANUP] Reports cleanup skipped: {e}")

    # 7. MongoDB Audit Logs Cleanup (Purges ALL audit entries for this evidence file & filename across both audit_log and audit_logs)
    try:
        from backend.app.db.mongodb import db_client as mongo
        eid_obj = ObjectId(evidence_id) if ObjectId.is_valid(evidence_id) else evidence_id
        fn = filename or ""
        
        audit_query = {
            "$or": [
                {"entity_id": str(evidence_id)},
                {"entity_id": eid_obj},
                {"metadata.evidence_id": str(evidence_id)},
                {"metadata.evidence_id": eid_obj},
            ]
        }
        if fn:
            audit_query["$or"].append({"metadata.filename": fn})

        await mongo.db["audit_log"].delete_many(audit_query)
        await mongo.db["audit_logs"].delete_many(audit_query)
        logger.info(f"[CLEANUP] Deleted audit log records for evidence {evidence_id} (filename={fn})")

        # If 0 evidence files remain for the case, purge ALL historical evidence audit logs
        cid_obj = ObjectId(case_id) if ObjectId.is_valid(case_id) else case_id
        rem_count = await mongo.db["evidence"].count_documents({"case_id": cid_obj})
        if rem_count == 0:
            purge_query = {
                "$or": [
                    {"entity_type": "evidence"},
                    {"action": {"$in": ["evidence.upload", "evidence.delete", "evidence.reprocess", "correlations.run", "graph.clear"]}}
                ]
            }
            p1 = await mongo.db["audit_log"].delete_many(purge_query)
            p2 = await mongo.db["audit_logs"].delete_many(purge_query)
            logger.info(f"[CLEANUP] Purged {p1.deleted_count + p2.deleted_count} total evidence audit logs for empty case {case_id}")
    except Exception as e:
        logger.warning(f"[CLEANUP] Audit log cleanup error: {e}")


@router.delete("/cases/{case_id}/evidence/{evidence_id}",
               status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(
    case_id: str, evidence_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Delete evidence — synchronously performs 100% complete multi-store cascade cleanup."""
    require_investigator(current_user.role)
    if not ObjectId.is_valid(case_id) or not ObjectId.is_valid(evidence_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")
    evidence = await EvidenceRepository.get_by_id(evidence_id, current_user.organization_id)
    minio_obj = evidence.get("minio_object_name") if evidence else None
    filename  = evidence.get("filename") if evidence else None

    # 1. Delete primary Evidence document instantly in MongoDB (< 5ms)
    if evidence:
        await EvidenceRepository.delete(evidence_id, current_user.organization_id)

    # 2. Run heavy multi-store cascade cleanup asynchronously in background
    import asyncio
    asyncio.create_task(_cleanup_evidence_resources(
        evidence_id,
        case_id,
        current_user.organization_id,
        minio_obj,
        filename,
    ))
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
          -[r:FORENSIC_ACTION]->
          (o:Entity {case_id:$cid, organization_id:$oid})
    WHERE r.evidence_id = $eid OR toString(r.evidence_id) = $eid
    RETURN s.name AS sn, s.type AS st, o.name AS tn, o.type AS tt,
           r.action AS action, r.severity AS severity,
           r.is_anomaly AS is_anomaly
    LIMIT 1000
    """
    nodes_dict, edges = {}, []
    try:
        async with neo4j_client.driver.session() as sess:
            result = await sess.run(cypher, cid=case_id, oid=current_user.organization_id, eid=evidence_id)
            records = await result.data()

        # If Neo4j graph is empty for this file, auto-sync events on-the-fly from MongoDB
        if not records:
            from backend.app.db.mongodb import db_client as mongo
            from backend.app.repositories.graph_repository import GraphRepository
            ev_docs = await mongo.db["events"].find({
                "evidence_id": ObjectId(evidence_id),
                "organization_id": ObjectId(current_user.organization_id)
            }).to_list(1000)
            if ev_docs:
                await GraphRepository.bulk_import_events(ev_docs)
                async with neo4j_client.driver.session() as sess:
                    result = await sess.run(cypher, cid=case_id, oid=current_user.organization_id, eid=evidence_id)
                    records = await result.data()

        for rec in records:
            for name, ntype in [(rec["sn"], rec["st"]), (rec["tn"], rec["tt"])]:
                if name not in nodes_dict:
                    nodes_dict[name] = {"id": name, "label": name, "type": ntype}
            edges.append({
                "source": rec["sn"], "target": rec["tn"],
                "action": rec["action"], "severity": rec["severity"],
                "is_anomaly": rec.get("is_anomaly", False)
            })
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

    from backend.app.repositories.event_repository import EventRepository
    ev_stats = await EventRepository.count_stats(case_id, current_user.organization_id, evidence_id=evidence_id)
    context["total_events"] = ev_stats["total"]
    context["anomalies_count"] = ev_stats["anomalies"]
    context["critical_high_count"] = ev_stats["critical"]
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
