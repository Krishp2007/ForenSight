"""
Audit Log API — ForenSight AI
"""
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from backend.app.repositories.audit_repository import AuditRepository
from backend.app.repositories.case_repository import CaseRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.rbac import require_viewer, require_admin
from backend.app.schemas.user import UserResponse

router = APIRouter(tags=["audit"])


async def _enrich_actor_details(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not rows:
        return rows
    actor_ids = set()
    for r in rows:
        aid = r.get("actor_id")
        if aid and ObjectId.is_valid(aid):
            actor_ids.add(ObjectId(aid))
    if not actor_ids:
        return rows

    from backend.app.db.mongodb import db_client
    users = await db_client.db["users"].find(
        {"_id": {"$in": list(actor_ids)}},
        {"name": 1, "email": 1}
    ).to_list(length=len(actor_ids))

    user_map = {}
    for u in users:
        uid = str(u["_id"])
        user_map[uid] = {
            "name": u.get("name") or u.get("email", "Investigator"),
            "email": u.get("email", "")
        }

    for r in rows:
        aid = str(r.get("actor_id", ""))
        if aid in user_map:
            r["actor_name"] = user_map[aid]["name"]
            r["actor_email"] = user_map[aid]["email"]
        else:
            r["actor_name"] = "Investigator" if aid else "System"
            r["actor_email"] = ""
    return rows


@router.get("/cases/{case_id}/audit", response_model=List[Dict[str, Any]])
async def get_case_audit_log(
    case_id: str,
    limit: int = 200,
    current_user: UserResponse = Depends(get_current_user),
):
    """Viewer+ can read the case audit trail."""
    require_viewer(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")
    rows = await AuditRepository.list_for_case(case_id, current_user.organization_id, limit=limit)
    return await _enrich_actor_details(rows)


@router.get("/audit", response_model=List[Dict[str, Any]])
async def get_org_audit_log(
    limit: int = 500,
    current_user: UserResponse = Depends(get_current_user),
):
    """Admin only — full org-wide audit log."""
    require_admin(current_user.role)
    rows = await AuditRepository.list_for_org(current_user.organization_id, limit=limit)
    return await _enrich_actor_details(rows)


@router.get("/audit/verify", response_model=Dict[str, Any])
async def verify_audit_chain(
    current_user: UserResponse = Depends(get_current_user),
):
    """Admin only — verify Merkle hash chain integrity."""
    require_admin(current_user.role)
    return await AuditRepository.verify_chain(current_user.organization_id)


@router.delete("/cases/{case_id}/audit")
async def clear_case_audit_log(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Investigator/Admin can purge evidence & correlation audit logs for a case."""
    from backend.app.auth.rbac import require_investigator
    from backend.app.db.mongodb import db_client as mongo
    require_investigator(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    cid_obj = ObjectId(case_id)
    query = {
        "$or": [
            {"entity_id": case_id},
            {"entity_id": cid_obj},
            {"metadata.case_id": case_id},
            {"metadata.case_id": cid_obj},
            {"entity_type": "evidence"},
            {"action": {"$regex": "^evidence\\."}},
            {"action": "correlations.run"},
            {"action": "graph.clear"}
        ]
    }
    # Purge from both collection names ('audit_log' and 'audit_logs')
    res1 = await mongo.db["audit_log"].delete_many(query)
    res2 = await mongo.db["audit_logs"].delete_many(query)
    total_deleted = res1.deleted_count + res2.deleted_count
    return {"message": f"Successfully purged {total_deleted} audit entries", "deleted_count": total_deleted}
