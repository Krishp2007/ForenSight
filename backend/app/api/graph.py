from fastapi import APIRouter, HTTPException, status, Depends, Query
from bson import ObjectId
import logging
from typing import Dict, Any, Optional, List

from backend.app.repositories.graph_repository import GraphRepository
from backend.app.repositories.case_repository import CaseRepository
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.rbac import require_investigator, require_viewer
from backend.app.schemas.user import UserResponse
from backend.app.services.graph.graph_correlation import GraphCorrelationEngine
from backend.app.services.graph.neo4j_service import neo4j_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["graph"])


@router.get("/debug/neo4j/{case_id}", response_model=Dict[str, Any])
async def debug_neo4j_state(case_id: str):
    """
    DEBUG: Full case_id pipeline diagnostic. No auth required (temporary debug endpoint).
    """
    from backend.app.db.mongodb import db_client
    from bson import ObjectId as BsonObjectId

    report: Dict[str, Any] = {"queried_case_id": case_id}

    try:
        # ── Neo4j totals ──────────────────────────────────────────────────────
        total_nodes_q = await neo4j_service.execute_query("MATCH (n) RETURN count(n) AS total")
        total_rels_q  = await neo4j_service.execute_query("MATCH ()-[r]->() RETURN count(r) AS total")
        report["neo4j_total_nodes"] = total_nodes_q[0]["total"] if total_nodes_q else 0
        report["neo4j_total_rels"]  = total_rels_q[0]["total"]  if total_rels_q  else 0

        # ── All distinct case_ids stored in Neo4j ─────────────────────────────
        node_case_ids_q = await neo4j_service.execute_query(
            "MATCH (n) WHERE n.case_id IS NOT NULL "
            "RETURN DISTINCT n.case_id AS stored_case_id, labels(n)[0] AS label "
            "ORDER BY stored_case_id LIMIT 20"
        )
        report["neo4j_distinct_case_ids_on_nodes"] = node_case_ids_q

        rel_case_ids_q = await neo4j_service.execute_query(
            "MATCH ()-[r]->() WHERE r.case_id IS NOT NULL "
            "RETURN DISTINCT r.case_id AS stored_case_id, type(r) AS rel_type "
            "ORDER BY stored_case_id LIMIT 20"
        )
        report["neo4j_distinct_case_ids_on_rels"] = rel_case_ids_q

        # ── Nodes with no case_id ─────────────────────────────────────────────
        null_case_q = await neo4j_service.execute_query(
            "MATCH (n) WHERE n.case_id IS NULL "
            "RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC"
        )
        report["neo4j_nodes_without_case_id"] = null_case_q

        # ── Nodes for the EXACT requested case_id ─────────────────────────────
        case_nodes_q = await neo4j_service.execute_query(
            "MATCH (n) WHERE n.case_id = $cid "
            "RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC",
            {"cid": case_id}
        )
        report["neo4j_nodes_for_queried_case_id"] = case_nodes_q
        report["neo4j_node_count_for_queried_case_id"] = sum(r["count"] for r in case_nodes_q)

        # ── Relationships for the EXACT requested case_id ─────────────────────
        case_rels_q = await neo4j_service.execute_query(
            "MATCH ()-[r]->() WHERE r.case_id = $cid "
            "RETURN type(r) AS rel_type, count(r) AS cnt ORDER BY cnt DESC LIMIT 20",
            {"cid": case_id}
        )
        report["neo4j_rels_for_queried_case_id"] = case_rels_q
        report["neo4j_rel_count_for_queried_case_id"] = sum(r["cnt"] for r in case_rels_q)

        # ── Graph query simulation (same query as get_case_graph) ─────────────
        graph_test_q = await neo4j_service.execute_query(
            "MATCH (s)-[r]->(t) "
            "WHERE (r.case_id = $cid OR s.case_id = $cid OR t.case_id = $cid) "
            "RETURN count(*) AS row_count",
            {"cid": case_id}
        )
        report["graph_query_rows_returned"] = graph_test_q[0]["row_count"] if graph_test_q else 0

        # ── MongoDB event counts ──────────────────────────────────────────────
        try:
            cid_obj = BsonObjectId(case_id) if BsonObjectId.is_valid(case_id) else None
            mongo_by_str = await db_client.db["events"].count_documents({"case_id": case_id})
            mongo_by_obj = await db_client.db["events"].count_documents({"case_id": cid_obj}) if cid_obj else 0
            mongo_total  = mongo_by_str + mongo_by_obj
            report["mongodb_events_by_str_case_id"] = mongo_by_str
            report["mongodb_events_by_obj_case_id"] = mongo_by_obj
            report["mongodb_events_total_for_case"] = mongo_total

            # Also check evidence docs for this case
            evidence_count = await db_client.db["evidence"].count_documents({
                "$or": [{"case_id": case_id}, {"case_id": cid_obj}] if cid_obj else [{"case_id": case_id}]
            })
            report["mongodb_evidence_count"] = evidence_count

            # Show distinct case_ids stored in MongoDB events
            distinct_cids = await db_client.db["events"].distinct("case_id")
            report["mongodb_distinct_case_ids"] = [str(c) for c in distinct_cids[:20]]

        except Exception as me:
            report["mongodb_error"] = str(me)

        # ── Diagnosis ─────────────────────────────────────────────────────────
        neo4j_count = report["neo4j_node_count_for_queried_case_id"]
        graph_rows  = report["graph_query_rows_returned"]
        mongo_count = report.get("mongodb_events_total_for_case", 0)

        if neo4j_count == 0 and graph_rows == 0 and mongo_count > 0:
            report["diagnosis"] = (
                f"MISMATCH: MongoDB has {mongo_count} events for case {case_id}, "
                f"but Neo4j has NO nodes for this case_id. "
                f"The pipeline processed these events but Neo4j sync did not store them under this case_id, "
                f"OR Neo4j sync failed silently. "
                f"Check the neo4j_distinct_case_ids_on_nodes to find what case_ids ARE stored. "
                f"Use POST /cases/{case_id}/graph/sync to re-sync events from MongoDB to Neo4j."
            )
        elif neo4j_count > 0 and graph_rows == 0:
            report["diagnosis"] = (
                f"Neo4j has {neo4j_count} nodes for this case_id but the graph query returns 0 rows. "
                f"All nodes may be isolated (no relationships). Check neo4j_rels_for_queried_case_id."
            )
        elif neo4j_count == 0 and mongo_count == 0:
            report["diagnosis"] = (
                f"Both MongoDB and Neo4j have no data for case {case_id}. "
                f"Either no evidence has been uploaded to this case, or evidence upload failed. "
                f"Upload evidence files to this case first."
            )
        elif graph_rows > 0:
            report["diagnosis"] = f"OK: Graph query returns {graph_rows} rows for case {case_id}. Graph should display correctly."
        else:
            report["diagnosis"] = "Unknown state — review all fields above."

        logger.info(
            f"[DEBUG] case_id={case_id} | "
            f"neo4j_nodes={neo4j_count} | neo4j_graph_rows={graph_rows} | "
            f"mongo_events={mongo_count}"
        )

    except Exception as e:
        report["error"] = str(e)
        logger.error(f"[DEBUG] debug_neo4j_state failed: {e}", exc_info=True)

    return report


@router.get("/debug/sync-and-verify/{case_id}", response_model=Dict[str, Any])
async def debug_sync_and_verify(case_id: str):
    """
    DEBUG: Runs the full graph sync for a case and immediately verifies what was written.
    No auth required. Use this to confirm the sync is actually working.
    Returns before/after node counts and a sample of what was written.
    """
    from backend.app.db.mongodb import db_client
    from bson import ObjectId as BsonObjectId
    from backend.app.repositories.graph_repository import GraphRepository

    result: Dict[str, Any] = {"case_id": case_id, "steps": []}

    try:
        # Step 1: Count nodes BEFORE sync
        before_q = await neo4j_service.execute_query(
            "MATCH (n) WHERE n.case_id = $cid RETURN count(n) AS cnt", {"cid": case_id}
        )
        nodes_before = before_q[0]["cnt"] if before_q else 0
        result["nodes_before_sync"] = nodes_before
        result["steps"].append(f"Before sync: {nodes_before} nodes for case_id={case_id}")

        # Step 2: Count MongoDB events
        cid_obj = BsonObjectId(case_id) if BsonObjectId.is_valid(case_id) else case_id
        mongo_count = await db_client.db["events"].count_documents({
            "$or": [{"case_id": case_id}, {"case_id": cid_obj}]
        })
        result["mongodb_event_count"] = mongo_count
        result["steps"].append(f"MongoDB has {mongo_count} events for this case_id")

        if mongo_count == 0:
            result["conclusion"] = "No events in MongoDB — nothing to sync. Upload and process evidence first."
            return result

        # Step 3: Fetch a sample event to inspect its fields
        sample = await db_client.db["events"].find_one({
            "$or": [{"case_id": case_id}, {"case_id": cid_obj}]
        })
        if sample:
            result["sample_event_fields"] = {
                "case_id": str(sample.get("case_id", "")),
                "case_id_type": type(sample.get("case_id")).__name__,
                "evidence_id": str(sample.get("evidence_id", "")),
                "evidence_id_type": type(sample.get("evidence_id")).__name__,
                "event_type": sample.get("event_type"),
                "source": sample.get("source"),
                "subject": sample.get("subject"),
                "action": sample.get("action"),
                "has_id": "_id" in sample,
            }
            result["steps"].append(f"Sample event: type={sample.get('event_type')} source={sample.get('source')} case_id_type={type(sample.get('case_id')).__name__}")

        # Step 4: Run the sync
        result["steps"].append("Running bulk_import_events...")
        cursor = db_client.db["events"].find({
            "$or": [{"case_id": case_id}, {"case_id": cid_obj}]
        })
        events = await cursor.to_list(length=mongo_count + 10)
        synced = await GraphRepository.bulk_import_events(events)
        result["synced_count"] = synced
        result["steps"].append(f"bulk_import_events returned: {synced}")

        # Step 5: Count nodes AFTER sync
        after_q = await neo4j_service.execute_query(
            "MATCH (n) WHERE n.case_id = $cid RETURN count(n) AS cnt", {"cid": case_id}
        )
        nodes_after = after_q[0]["cnt"] if after_q else 0
        result["nodes_after_sync"] = nodes_after
        result["steps"].append(f"After sync: {nodes_after} nodes for case_id={case_id}")

        # Step 6: Count relationships after sync
        rels_after_q = await neo4j_service.execute_query(
            "MATCH (s)-[r]->(t) WHERE s.case_id = $cid OR r.case_id = $cid OR t.case_id = $cid "
            "RETURN count(r) AS cnt", {"cid": case_id}
        )
        rels_after = rels_after_q[0]["cnt"] if rels_after_q else 0
        result["rels_after_sync"] = rels_after
        result["steps"].append(f"After sync: {rels_after} relationships for case_id={case_id}")

        # Step 7: Test the exact same query used by get_case_graph
        graph_q = await neo4j_service.execute_query(
            "MATCH (s)-[r]->(t) WHERE (r.case_id = $cid OR s.case_id = $cid OR t.case_id = $cid) "
            "RETURN count(*) AS cnt", {"cid": case_id}
        )
        graph_rows = graph_q[0]["cnt"] if graph_q else 0
        result["graph_query_rows"] = graph_rows
        result["steps"].append(f"Graph MATCH query returns: {graph_rows} rows")

        # Step 8: Direct write test — write and read back one test node
        test_cid = f"__debug_test_{case_id}"
        await neo4j_service.execute_query(
            "MERGE (n:DebugTest {debug_id: $did}) SET n.case_id = $cid",
            {"did": test_cid, "cid": case_id}
        )
        test_read = await neo4j_service.execute_query(
            "MATCH (n:DebugTest {debug_id: $did}) RETURN n.case_id AS cid",
            {"did": test_cid}
        )
        result["direct_write_test"] = {
            "wrote_case_id": case_id,
            "read_back_case_id": test_read[0]["cid"] if test_read else None,
            "write_works": bool(test_read and test_read[0]["cid"] == case_id),
        }
        # Clean up test node
        await neo4j_service.execute_query(
            "MATCH (n:DebugTest {debug_id: $did}) DELETE n", {"did": test_cid}
        )
        result["steps"].append(f"Direct write test: {result['direct_write_test']}")

        # Conclusion
        if nodes_after > nodes_before:
            result["conclusion"] = f"SYNC WORKED: {nodes_after - nodes_before} new nodes written. Graph query returns {graph_rows} rows."
        elif nodes_after == 0 and result["direct_write_test"]["write_works"]:
            result["conclusion"] = (
                f"SYNC DID NOT WRITE NODES but direct writes work. "
                f"The Cypher MERGE may be silently failing. Check that event_id is non-empty in sample_event_fields. "
                f"bulk_import_events returned {synced} — if 0, no events passed the event_id filter."
            )
        elif not result["direct_write_test"]["write_works"]:
            result["conclusion"] = "DIRECT WRITE FAILED — Neo4j connection is working for reads but writes are not being persisted. Check Neo4j logs."
        else:
            result["conclusion"] = f"Nodes before={nodes_before} after={nodes_after}. Graph rows={graph_rows}. Check steps for details."

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"[DEBUG] sync_and_verify failed: {e}", exc_info=True)

    return result


@router.get("/cases/{case_id}/graph", response_model=Dict[str, Any])
async def get_case_graph(
    case_id: str,
    limit: int = Query(1000, ge=1, le=5000),
    anomaly_only: bool = Query(False),
    current_user: UserResponse = Depends(get_current_user),
):
    """Retrieve Neo4j node-link visualization graph for a case. Viewer+"""
    require_viewer(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    logger.info(
        f"[GRAPH API] GET /cases/{case_id}/graph "
        f"limit={limit} anomaly_only={anomaly_only} "
        f"user={current_user.id} org={current_user.organization_id}"
    )

    try:
        result = await GraphRepository.get_case_graph(
            case_id, current_user.organization_id, limit=limit, anomaly_only=anomaly_only
        )
        node_count = len(result.get("nodes", []))
        edge_count = len(result.get("edges", []))
        logger.info(
            f"[GRAPH API] case={case_id} → {node_count} nodes, {edge_count} edges returned to frontend"
        )
        if node_count == 0:
            logger.warning(
                f"[GRAPH API] ZERO nodes returned for case={case_id}. "
                f"Check /debug/neo4j/{case_id} for pipeline diagnosis. "
                f"If Neo4j has data under a different case_id, use POST /cases/{case_id}/graph/sync to re-sync."
            )
        return result
    except Exception as e:
        logger.error(f"[GRAPH API] Graph fetch failed for case={case_id}: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Neo4j error: {e}")


@router.get("/evidence/{evidence_id}/graph", response_model=Dict[str, Any])
@router.get("/cases/{case_id}/evidence/{evidence_id}/graph", response_model=Dict[str, Any])
async def get_evidence_graph(
    evidence_id: str,
    case_id: Optional[str] = None,
    limit: int = Query(500, ge=1, le=2000),
    current_user: UserResponse = Depends(get_current_user),
):
    """Retrieve graph relationships originating from a specific evidence file. Viewer+"""
    require_viewer(current_user.role)
    if not ObjectId.is_valid(evidence_id):
        raise HTTPException(status_code=400, detail="Invalid evidence ID format")

    ev = await EvidenceRepository.get_by_id(evidence_id, current_user.organization_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence file not found")

    try:
        return await GraphRepository.get_case_graph(
            case_id=str(ev["case_id"]),
            org_id=current_user.organization_id,
            evidence_id=evidence_id,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Evidence graph fetch failed: {e}")
        raise HTTPException(status_code=503, detail=f"Neo4j error: {e}")


@router.get("/events/{event_id}/graph", response_model=Dict[str, Any])
async def get_event_neighborhood(
    event_id: str,
    depth: int = Query(2, ge=1, le=4),
    current_user: UserResponse = Depends(get_current_user),
):
    """Retrieve local graph neighborhood around a specific event ID. Viewer+"""
    require_viewer(current_user.role)
    cypher = f"""
    MATCH path = (e:Event {{event_id: $event_id}})-[*1..{depth}]-(neighbor)
    RETURN
        labels(neighbor)[0] AS node_type,
        coalesce(neighbor.process_id, neighbor.user_id, neighbor.host_id, neighbor.address, neighbor.domain_name, neighbor.file_id, neighbor.event_id) AS node_id,
        neighbor AS properties
    LIMIT 100
    """
    try:
        records = await neo4j_service.execute_query(cypher, {"event_id": event_id})
        nodes = []
        for r in records:
            nodes.append({
                "id": f"{str(r['node_type']).lower()}:{r['node_id']}",
                "type": r["node_type"],
                "properties": dict(r["properties"] or {}),
            })
        return {"event_id": event_id, "depth": depth, "nodes": nodes}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j error: {e}")


@router.get("/cases/{case_id}/attack-paths", response_model=Dict[str, Any])
async def get_case_attack_paths(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Retrieve detected attack chains and suspicious graph paths. Viewer+"""
    require_viewer(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")

    try:
        paths = await GraphCorrelationEngine.detect_suspicious_paths(case_id)
        chains = await GraphCorrelationEngine.detect_process_chains(case_id)
        return {"case_id": case_id, "attack_paths": paths, "process_chains": chains}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Attack path query failed: {e}")


@router.get("/cases/{case_id}/graph/analytics", response_model=Dict[str, Any])
async def get_case_graph_analytics(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Graph structural analytics. Viewer+"""
    require_viewer(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    try:
        from backend.app.services.graph.graph_analytics import GraphAnalytics
        return await GraphAnalytics.full_summary(case_id, current_user.organization_id)
    except Exception as e:
        logger.error(f"Graph analytics failed: {e}")
        raise HTTPException(status_code=503, detail=f"Neo4j error: {e}")


@router.post("/cases/{case_id}/graph/sync", response_model=Dict[str, Any])
async def sync_case_graph(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Push MongoDB events -> Neo4j. Investigator+"""
    require_investigator(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    logger.info(f"[GRAPH SYNC] POST /cases/{case_id}/graph/sync — user={current_user.id}")

    try:
        from backend.app.repositories.event_repository import EventRepository
        from backend.app.repositories.evidence_repository import EvidenceRepository
        from bson import ObjectId as BsonObjectId
        from backend.app.db.mongodb import db_client

        ev_items = await EvidenceRepository.list_by_case(case_id, current_user.organization_id)
        if not ev_items:
            await GraphRepository.clear_case_graph(case_id, current_user.organization_id)
            logger.warning(f"[GRAPH SYNC] No evidence for case={case_id}. Cleared graph.")
            return {"synced": 0, "total_events": 0, "detail": "No evidence files exist for this case."}

        # Count total events first to handle large datasets
        cid_obj = BsonObjectId(case_id) if BsonObjectId.is_valid(case_id) else case_id
        total_count = await db_client.db["events"].count_documents({
            "$or": [{"case_id": case_id}, {"case_id": cid_obj}]
        })
        logger.info(f"[GRAPH SYNC] case={case_id} has {total_count} events in MongoDB")

        if total_count == 0:
            logger.warning(f"[GRAPH SYNC] Zero events in MongoDB for case={case_id}")
            return {"synced": 0, "total_events": 0, "detail": "No events found in MongoDB for this case."}

        # Stream events in batches to handle datasets larger than 10,000 events
        BATCH_SIZE = 5000
        total_synced = 0
        batch_num = 0

        cursor = db_client.db["events"].find({
            "$or": [{"case_id": case_id}, {"case_id": cid_obj}]
        }).sort("timestamp", 1)

        batch: list = []
        async for event in cursor:
            batch.append(event)
            if len(batch) >= BATCH_SIZE:
                batch_num += 1
                logger.info(f"[GRAPH SYNC] Syncing batch {batch_num} ({len(batch)} events) for case={case_id}")
                synced = await GraphRepository.bulk_import_events(batch)
                total_synced += synced
                batch.clear()

        # Flush remaining events
        if batch:
            batch_num += 1
            logger.info(f"[GRAPH SYNC] Syncing final batch {batch_num} ({len(batch)} events) for case={case_id}")
            synced = await GraphRepository.bulk_import_events(batch)
            total_synced += synced

        logger.info(
            f"[GRAPH SYNC] COMPLETE case={case_id} — "
            f"total_events={total_count} synced={total_synced} batches={batch_num}"
        )
        return {"synced": total_synced, "total_events": total_count}

    except Exception as e:
        logger.error(f"[GRAPH SYNC] Sync failed for case={case_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sync failed: {e}")


def _enrich_node_metadata(n_type: str, label: str, props: dict) -> dict:
    lbl_lower = (label or "").lower()
    mitre = []
    explanation = ""
    suspicious = False
    risk_level = "low"

    if n_type == "Process":
        if any(p in lbl_lower for p in ["powershell.exe", "powershell"]):
            mitre.append({"id": "T1059.001", "name": "PowerShell", "tactic": "Execution"})
            explanation = "PowerShell execution detected. Scripting interpreters are commonly leveraged by attackers to execute payloads, bypass execution policies, and run in-memory commands."
            suspicious = True
            risk_level = "high"
        elif any(p in lbl_lower for p in ["cmd.exe", "cmd"]):
            mitre.append({"id": "T1059.003", "name": "Windows Command Shell", "tactic": "Execution"})
            explanation = "Windows Command Shell executed. Frequently spawned in attack chains for system enumeration and execution."
            suspicious = True
            risk_level = "medium"
        elif any(p in lbl_lower for p in ["wmic.exe", "wmic"]):
            mitre.append({"id": "T1047", "name": "WMI", "tactic": "Execution"})
            explanation = "WMI execution detected. Often used by adversary tools for remote execution, system reconnaissance, and persistence."
            suspicious = True
            risk_level = "high"
        elif any(p in lbl_lower for p in ["schtasks.exe", "at.exe"]):
            mitre.append({"id": "T1053.005", "name": "Scheduled Task", "tactic": "Persistence"})
            explanation = "Scheduled Task configuration utility executed. Commonly used for persistence and privilege escalation."
            suspicious = True
            risk_level = "high"
        elif any(p in lbl_lower for p in ["mshta.exe", "regsvr32.exe", "rundll32.exe"]):
            mitre.append({"id": "T1218", "name": "System Binary Proxy Execution", "tactic": "Defense Evasion"})
            explanation = "Lolbin proxy binary execution detected. Used to bypass application whitelisting and execute arbitrary scripts."
            suspicious = True
            risk_level = "critical"
        elif any(p in lbl_lower for p in ["certutil.exe", "bitsadmin.exe"]):
            mitre.append({"id": "T1105", "name": "Ingress Tool Transfer", "tactic": "Command and Control"})
            explanation = "Ingress tool transfer utility executed. Used to download external malicious payloads."
            suspicious = True
            risk_level = "critical"
        elif any(p in lbl_lower for p in ["reg.exe"]):
            mitre.append({"id": "T1112", "name": "Modify Registry", "tactic": "Defense Evasion"})
            explanation = "Registry modification via reg.exe detected. Frequently used to establish persistence."
            suspicious = True
            risk_level = "medium"
        elif any(p in lbl_lower for p in ["net.exe", "net1.exe"]):
            mitre.append({"id": "T1087", "name": "Account Discovery", "tactic": "Discovery"})
            explanation = "Network/account discovery utility executed."
            suspicious = True
            risk_level = "medium"

    elif n_type == "IPAddress":
        is_priv = props.get("is_private", False)
        if not is_priv:
            mitre.append({"id": "T1071", "name": "Application Layer Protocol", "tactic": "Command and Control"})
            explanation = f"Outbound connection to public IP ({label}). External non-private communication."
            suspicious = True
            risk_level = "medium"

    elif n_type == "Domain":
        mitre.append({"id": "T1568", "name": "Dynamic Resolution", "tactic": "Command and Control"})
        explanation = f"Domain name resolution ({label}). Remote network destination."
        risk_level = "info"

    elif n_type == "RegistryKey":
        path_lower = (props.get("path") or label).lower()
        if any(k in path_lower for k in ["run", "runonce", "winlogon", "startup"]):
            mitre.append({"id": "T1547.001", "name": "Registry Run Keys", "tactic": "Persistence"})
            explanation = "Autostart registry persistence mechanism modification detected."
            suspicious = True
            risk_level = "high"

    score = float(props.get("anomaly_score") or 0.0)
    is_anom = bool(props.get("is_anomaly", False))
    if is_anom or score > 0.75:
        risk_level = "critical"
        suspicious = True
        if not explanation:
            explanation = f"ML ensemble anomaly detector flagged this node with high suspicion score ({score:.2f})."
    elif score > 0.5:
        if risk_level not in ("critical", "high"):
            risk_level = "high"
        suspicious = True
        if not explanation:
            explanation = f"Elevated anomaly score ({score:.2f}) detected."

    return {
        "mitre_attack": mitre,
        "explanation": explanation,
        "suspicious": suspicious,
        "risk_level": risk_level,
    }


@router.get("/cases/{case_id}/graph/summary", response_model=Dict[str, Any])
async def get_case_graph_summary(
    case_id: str,
    view: str = Query("entity"),
    evidence_id: Optional[str] = Query(None),
    anomaly_only: bool = Query(False),
    hide_benign: bool = Query(False),
    severity: Optional[str] = Query(None),
    search_query: Optional[str] = Query(None),
    source_node: Optional[str] = Query(None),
    target_node: Optional[str] = Query(None),
    limit: int = Query(2000, ge=1, le=10000),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Investigator-centric aggregated graph endpoint.
    Returns semantic entity relationships (NOT raw Event nodes).
    Aggregates duplicate connections into edge counts.
    Supports 8 DFIR views: entity, process_tree, attack_path, network, browser, registry, auth, ioc.
    Includes benign activity filtering, search matching, MITRE ATT&CK enrichment, and path finding.
    """
    require_viewer(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")
    case = await CaseRepository.get_by_id(case_id, current_user.organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    valid_views = {"entity", "process_tree", "attack_path", "network", "browser", "registry", "auth", "ioc"}
    if view not in valid_views:
        view = "entity"

    logger.info(f"[GRAPH SUMMARY] case={case_id} view={view} anomaly_only={anomaly_only} hide_benign={hide_benign}")

    try:
        params: Dict[str, Any] = {"case_id": case_id, "limit": limit}

        # ── Evidence-scoped subgraph anchoring ────────────────────────────────
        ev_filter = ""
        ev_id_filter_node = ""   # injected into node-level WHERE for entity views
        ev_id_filter_rel  = ""   # injected for relationship-level filters

        if evidence_id and ObjectId.is_valid(evidence_id):
            params["evidence_id"] = evidence_id
            ev_id_filter_rel = "AND (r.evidence_id = $evidence_id OR n.evidence_id = $evidence_id OR m.evidence_id = $evidence_id)"
            ev_id_filter_node = "AND (r.evidence_id = $evidence_id OR n.evidence_id = $evidence_id OR m.evidence_id = $evidence_id)"
            ev_filter = ev_id_filter_rel

        anomaly_filter = ""
        if anomaly_only:
            anomaly_filter = """
            AND (
                n.is_anomaly = true OR n.anomaly_score > 0.5 OR
                m.is_anomaly = true OR m.anomaly_score > 0.5 OR
                r.is_anomaly = true OR r.anomaly_score > 0.5
            )
            """

        benign_filter = ""
        if hide_benign:
            benign_filter = """
            AND NOT (toLower(coalesce(n.process_name, n.label, '')) IN ['svchost.exe', 'conhost.exe', 'lsass.exe', 'explorer.exe', 'smss.exe', 'csrss.exe', 'services.exe', 'wininit.exe', 'taskhostw.exe', 'searchindexer.exe', 'fontdrvhost.exe', 'dwm.exe', 'ctfmon.exe', 'spoolsv.exe'])
            AND NOT (toLower(coalesce(m.process_name, m.label, '')) IN ['svchost.exe', 'conhost.exe', 'lsass.exe', 'explorer.exe', 'smss.exe', 'csrss.exe', 'services.exe', 'wininit.exe', 'taskhostw.exe', 'searchindexer.exe', 'fontdrvhost.exe', 'dwm.exe', 'ctfmon.exe', 'spoolsv.exe'])
            """

        sev_filter = ""
        if severity and severity in ("critical", "high", "medium", "low", "info"):
            severity_levels = []
            if severity == "critical":
                severity_levels = ["critical"]
            elif severity == "high":
                severity_levels = ["critical", "high"]
            elif severity == "medium":
                severity_levels = ["critical", "high", "medium"]
            elif severity == "low":
                severity_levels = ["critical", "high", "medium", "low"]
            else:
                severity_levels = ["critical", "high", "medium", "low", "info"]
            
            # Make case-insensitive match lists
            severity_levels += [s.upper() for s in severity_levels] + [s.capitalize() for s in severity_levels]
            params["severity_levels"] = list(set(severity_levels))
            sev_filter = "AND (n.severity IN $severity_levels OR m.severity IN $severity_levels)"

        search_clause = ""
        if search_query:
            import re
            params["sq"] = f"(?i).*{re.escape(search_query)}.*"
            search_clause = """
            AND (
                coalesce(n.process_name, n.username, n.hostname, n.address, n.domain_name, n.path, '') =~ $sq OR
                coalesce(m.process_name, m.username, m.hostname, m.address, m.domain_name, m.path, '') =~ $sq
            )
            """

        # ── View-specific Cypher queries ──────────────────────────────────────
        if view == "process_tree":
            cypher = f"""
            MATCH (n)-[r:SPAWNED|EXECUTED|INVOLVES_PROCESS|OCCURRED_ON|INVOLVES_USER]->(m)
            WHERE (n.case_id = $case_id OR m.case_id = $case_id)
            {ev_id_filter_rel} {anomaly_filter} {benign_filter} {sev_filter} {search_clause}
            WITH n, m, type(r) AS rel_type,
                 collect(properties(r))[0] AS rel_props, count(r) AS edge_count
            RETURN
                labels(n)[0] AS source_type,
                coalesce(n.process_id, n.user_id, n.host_id, n.event_id, n.evidence_id, n.case_id) AS source_id,
                coalesce(n.process_name, n.username, n.hostname, n.event_type, n.case_id) AS source_label,
                properties(n) AS source_props,
                rel_type, rel_props,
                labels(m)[0] AS target_type,
                coalesce(m.process_id, m.user_id, m.host_id, m.event_id, m.evidence_id, m.case_id) AS target_id,
                coalesce(m.process_name, m.username, m.hostname, m.event_type, m.case_id) AS target_label,
                properties(m) AS target_props,
                edge_count
            LIMIT $limit
            """

        elif view == "attack_path":
            cypher = f"""
            MATCH (n)-[r:SPAWNED|CONNECTED_TO|RESOLVED|MODIFIED_REGISTRY|EXECUTED|CREATED]->(m)
            WHERE (n.case_id = $case_id OR m.case_id = $case_id)
              AND (
                  n.is_anomaly = true OR n.anomaly_score > 0.4 OR
                  m.is_anomaly = true OR m.anomaly_score > 0.4 OR
                  r.is_anomaly = true OR r.anomaly_score > 0.4 OR
                  toLower(coalesce(n.process_name, '')) IN ['powershell.exe', 'cmd.exe', 'wmic.exe', 'mshta.exe', 'schtasks.exe', 'regsvr32.exe', 'certutil.exe'] OR
                  toLower(coalesce(m.process_name, '')) IN ['powershell.exe', 'cmd.exe', 'wmic.exe', 'mshta.exe', 'schtasks.exe', 'regsvr32.exe', 'certutil.exe']
              )
            {ev_id_filter_rel} {benign_filter} {search_clause}
            WITH n, m, type(r) AS rel_type,
                 collect(properties(r))[0] AS rel_props, count(r) AS edge_count
            RETURN
                labels(n)[0] AS source_type,
                coalesce(n.process_id, n.user_id, n.host_id, n.ip_id, n.domain_id, n.case_id) AS source_id,
                coalesce(n.process_name, n.username, n.hostname, n.address, n.domain_name, n.case_id) AS source_label,
                properties(n) AS source_props,
                rel_type, rel_props,
                labels(m)[0] AS target_type,
                coalesce(m.process_id, m.user_id, m.host_id, m.ip_id, m.domain_id, m.case_id) AS target_id,
                coalesce(m.process_name, m.username, m.hostname, m.address, m.domain_name, m.case_id) AS target_label,
                properties(m) AS target_props,
                edge_count
            LIMIT $limit
            """

        elif view == "network":
            cypher = f"""
            MATCH (n)-[r:CONNECTED_TO|RESOLVED|RESOLVES_TO|USES_PORT|VISITED_DOMAIN|CONTAINS_VISIT]->(m)
            WHERE (n.case_id = $case_id OR m.case_id = $case_id)
            {ev_id_filter_rel} {anomaly_filter} {benign_filter} {sev_filter} {search_clause}
            WITH n, m, type(r) AS rel_type,
                 collect(properties(r))[0] AS rel_props, count(r) AS edge_count
            RETURN
                labels(n)[0] AS source_type,
                coalesce(n.process_id, n.host_id, n.ip_id, n.domain_id, n.event_id, n.evidence_id) AS source_id,
                coalesce(n.process_name, n.hostname, n.address, n.domain_name, n.url, n.event_type) AS source_label,
                properties(n) AS source_props,
                rel_type, rel_props,
                labels(m)[0] AS target_type,
                coalesce(m.ip_id, m.domain_id, m.port_id, m.event_id) AS target_id,
                coalesce(m.address, m.domain_name, m.url) AS target_label,
                properties(m) AS target_props,
                edge_count
            LIMIT $limit
            """

        elif view == "browser":
            cypher = f"""
            MATCH (n)-[r:VISITED_DOMAIN|CONTAINS_VISIT]->(m)
            WHERE (n.case_id = $case_id OR m.case_id = $case_id OR r.case_id = $case_id)
            {ev_id_filter_rel} {anomaly_filter} {search_clause}
            WITH n, m, type(r) AS rel_type,
                 collect(properties(r))[0] AS rel_props, count(r) AS edge_count
            RETURN
                labels(n)[0] AS source_type,
                coalesce(n.domain_id, n.domain_name, n.event_id, n.evidence_id, n.case_id) AS source_id,
                coalesce(n.domain_name, n.url, n.title, n.event_type, n.case_id) AS source_label,
                properties(n) AS source_props,
                rel_type, rel_props,
                labels(m)[0] AS target_type,
                coalesce(m.domain_id, m.domain_name, m.event_id) AS target_id,
                coalesce(m.domain_name, m.url) AS target_label,
                properties(m) AS target_props,
                edge_count
            LIMIT $limit
            """

        elif view == "registry":
            cypher = f"""
            MATCH (n)-[r:MODIFIED_REGISTRY|MODIFIED|INVOLVES_REGISTRY]->(m)
            WHERE (n.case_id = $case_id OR m.case_id = $case_id OR r.case_id = $case_id)
              AND ('RegistryKey' IN labels(n) OR 'RegistryKey' IN labels(m))
            {ev_id_filter_rel} {anomaly_filter} {benign_filter} {sev_filter} {search_clause}
            WITH n, m, count(r) AS edge_count,
                 collect(properties(r))[0] AS rel_props
            RETURN
                labels(n)[0] AS source_type,
                coalesce(n.process_id, n.host_id, n.reg_id, n.event_id, n.case_id) AS source_id,
                coalesce(n.process_name, n.hostname, n.path, 'Registry Entity') AS source_label,
                properties(n) AS source_props,
                type(r) AS rel_type,
                rel_props,
                labels(m)[0] AS target_type,
                coalesce(m.reg_id, m.process_id, m.event_id) AS target_id,
                coalesce(m.path, m.process_name, 'Registry Key') AS target_label,
                properties(m) AS target_props,
                edge_count
            LIMIT $limit
            """

        elif view == "auth":
            cypher = f"""
            MATCH (n)-[r:INVOLVES_USER|EXECUTED|OCCURRED_ON|LOGGED_IN]->(m)
            WHERE (n.case_id = $case_id OR m.case_id = $case_id OR r.case_id = $case_id)
              AND ('User' IN labels(n) OR 'User' IN labels(m) OR 'Host' IN labels(n) OR 'Host' IN labels(m))
            {ev_id_filter_rel} {anomaly_filter} {benign_filter} {sev_filter} {search_clause}
            WITH n, m, type(r) AS rel_type,
                 collect(properties(r))[0] AS rel_props, count(r) AS edge_count
            RETURN
                labels(n)[0] AS source_type,
                coalesce(n.user_id, n.host_id, n.process_id, n.case_id) AS source_id,
                coalesce(n.username, n.hostname, n.process_name, n.case_id) AS source_label,
                properties(n) AS source_props,
                rel_type, rel_props,
                labels(m)[0] AS target_type,
                coalesce(m.user_id, m.host_id, m.process_id, m.case_id) AS target_id,
                coalesce(m.username, m.hostname, m.process_name, m.case_id) AS target_label,
                properties(m) AS target_props,
                edge_count
            LIMIT $limit
            """

        elif view == "ioc":
            cypher = f"""
            MATCH (n)-[r]->(m)
            WHERE (n.case_id = $case_id OR m.case_id = $case_id OR r.case_id = $case_id)
              AND (
                  n.is_anomaly = true OR n.anomaly_score > 0.5 OR
                  m.is_anomaly = true OR m.anomaly_score > 0.5 OR
                  r.is_anomaly = true OR r.anomaly_score > 0.5
              )
              {ev_id_filter_rel} {benign_filter} {sev_filter} {search_clause}
            WITH n, m, type(r) AS rel_type,
                 collect(properties(r))[0] AS rel_props, count(r) AS edge_count
            RETURN
                labels(n)[0] AS source_type,
                coalesce(n.process_id, n.user_id, n.host_id, n.ip_id, n.domain_id, n.file_id, n.event_id, n.case_id) AS source_id,
                coalesce(n.process_name, n.username, n.hostname, n.address, n.domain_name, n.event_type, n.case_id) AS source_label,
                properties(n) AS source_props,
                rel_type, rel_props,
                labels(m)[0] AS target_type,
                coalesce(m.process_id, m.user_id, m.host_id, m.ip_id, m.domain_id, m.file_id, m.event_id, m.case_id) AS target_id,
                coalesce(m.process_name, m.username, m.hostname, m.address, m.domain_name, m.event_type, m.case_id) AS target_label,
                properties(m) AS target_props,
                edge_count
            LIMIT $limit
            """

        else:  # "entity" — default aggregated entity graph, no raw Event nodes
            cypher = f"""
            MATCH (n)-[r]->(m)
            WHERE (n.case_id = $case_id OR m.case_id = $case_id OR r.case_id = $case_id)
              AND NOT 'Event' IN labels(n)
              AND NOT 'Event' IN labels(m)
              AND NOT 'Case' IN labels(n)
              AND NOT 'Case' IN labels(m)
              {ev_id_filter_node} {anomaly_filter} {benign_filter} {sev_filter} {search_clause}
            WITH n, m, type(r) AS rel_type,
                 collect(properties(r))[0] AS rel_props,
                 count(r) AS edge_count
            RETURN
                labels(n)[0] AS source_type,
                coalesce(n.process_id, n.user_id, n.host_id, n.ip_id, n.domain_id,
                         n.reg_id, n.file_id, n.service_id, n.evidence_id, n.case_id) AS source_id,
                coalesce(n.process_name, n.username, n.hostname, n.address,
                         n.domain_name, n.path, n.service_name, n.evidence_id) AS source_label,
                properties(n) AS source_props,
                rel_type,
                rel_props,
                labels(m)[0] AS target_type,
                coalesce(m.process_id, m.user_id, m.host_id, m.ip_id, m.domain_id,
                         m.reg_id, m.file_id, m.service_id, m.evidence_id, m.case_id) AS target_id,
                coalesce(m.process_name, m.username, m.hostname, m.address,
                         m.domain_name, m.path, m.service_name, m.evidence_id) AS target_label,
                properties(m) AS target_props,
                edge_count
            LIMIT $limit
            """

        records = await neo4j_service.execute_query(cypher, params)
        logger.info(f"[GRAPH SUMMARY] view={view} → {len(records)} rows")

        # Build aggregated node/edge response
        def _safe(obj):
            if obj is None: return {}
            if isinstance(obj, dict): return obj
            if hasattr(obj, '_properties'): return dict(obj._properties)
            if hasattr(obj, 'items'):
                try: return dict(obj.items())
                except: return {}
            if hasattr(obj, 'keys'):
                try: return {k: obj[k] for k in obj.keys()}
                except: return {}
            return {}

        nodes_dict: Dict[str, Any] = {}
        edges_dict: Dict[str, Any] = {}

        for row in records:
            s_id = str(row.get("source_id") or "")
            t_id = str(row.get("target_id") or "")
            if not s_id or not t_id:
                continue

            s_type = str(row.get("source_type") or "Entity")
            t_type = str(row.get("target_type") or "Entity")
            s_label = str(row.get("source_label") or s_id)[:80]
            t_label = str(row.get("target_label") or t_id)[:80]
            s_props = _safe(row.get("source_props"))
            t_props = _safe(row.get("target_props"))
            r_props = _safe(row.get("rel_props"))
            edge_count = int(row.get("edge_count") or 1)

            s_node_id = f"{s_type.lower()}:{s_id}"
            t_node_id = f"{t_type.lower()}:{t_id}"

            if s_node_id not in nodes_dict:
                s_meta = _enrich_node_metadata(s_type, s_label, s_props)
                nodes_dict[s_node_id] = {
                    "id": s_node_id, "raw_id": s_id, "type": s_type,
                    "label": s_label, "properties": s_props,
                    "is_anomaly": bool(s_props.get("is_anomaly", False) or s_meta["suspicious"]),
                    "anomaly_score": float(s_props.get("anomaly_score") or 0),
                    "severity": s_props.get("severity", s_meta["risk_level"]),
                    "mitre_attack": s_meta["mitre_attack"],
                    "explanation": s_meta["explanation"],
                    "suspicious": s_meta["suspicious"],
                    "risk_level": s_meta["risk_level"],
                }

            if t_node_id not in nodes_dict:
                t_meta = _enrich_node_metadata(t_type, t_label, t_props)
                nodes_dict[t_node_id] = {
                    "id": t_node_id, "raw_id": t_id, "type": t_type,
                    "label": t_label, "properties": t_props,
                    "is_anomaly": bool(t_props.get("is_anomaly", False) or t_meta["suspicious"]),
                    "anomaly_score": float(t_props.get("anomaly_score") or 0),
                    "severity": t_props.get("severity", t_meta["risk_level"]),
                    "mitre_attack": t_meta["mitre_attack"],
                    "explanation": t_meta["explanation"],
                    "suspicious": t_meta["suspicious"],
                    "risk_level": t_meta["risk_level"],
                }

            rel_type = str(row.get("rel_type") or "RELATES_TO")
            edge_key = f"{s_node_id}->{t_node_id}:{rel_type}"

            if edge_key not in edges_dict:
                edges_dict[edge_key] = {
                    "id": f"edge-{len(edges_dict)+1}",
                    "source": s_node_id,
                    "target": t_node_id,
                    "type": rel_type,
                    "count": edge_count,
                    "is_anomaly": bool(
                        r_props.get("is_anomaly", False) or
                        nodes_dict[s_node_id]["is_anomaly"] or
                        nodes_dict[t_node_id]["is_anomaly"]
                    ),
                    "properties": r_props,
                }
            else:
                edges_dict[edge_key]["count"] += edge_count
                if r_props.get("is_anomaly", False):
                    edges_dict[edge_key]["is_anomaly"] = True

        edges = list(edges_dict.values())
        logger.info(f"[GRAPH SUMMARY] Built {len(nodes_dict)} nodes, {len(edges)} aggregated edges for view={view}")
        return {
            "nodes": list(nodes_dict.values()),
            "edges": edges,
            "view": view,
            "total_nodes": len(nodes_dict),
            "total_edges": len(edges),
        }

    except Exception as e:
        logger.error(f"[GRAPH SUMMARY] Failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Graph summary error: {e}")
async def clear_case_graph(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Clear Neo4j graph nodes and relationships for a case. Investigator+"""
    require_investigator(current_user.role)
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")

    await GraphRepository.clear_case_graph(case_id, current_user.organization_id)
    await AuditRepository.log(
        actor_id=current_user.id,
        org_id=current_user.organization_id,
        action="graph.clear",
        entity_type="case",
        entity_id=case_id,
    )
    return None
