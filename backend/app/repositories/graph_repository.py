import logging
import re
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from bson import ObjectId
from backend.app.services.graph.neo4j_service import neo4j_service

logger = logging.getLogger(__name__)

IP_PATTERN = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$")
FILE_EXT_PATTERN = re.compile(r"\.[a-zA-Z0-9]{2,4}$")

# ─── Browser-specific Cypher ──────────────────────────────────────────────────
# Creates BrowserVisit + Domain nodes. Does NOT create fake Process/Host/User.
# All nodes scoped by case_id for tenant isolation.
# MERGE on Domain.domain_id ensures deduplication across repeated visits.
_BROWSER_CYPHER = """
UNWIND $batch AS ev

// 1. Core hierarchy: Case -> Evidence
MERGE (c:Case {case_id: ev.case_id})
MERGE (e:Evidence {evidence_id: ev.evidence_id})
SET e.case_id = ev.case_id
MERGE (c)-[:HAS_EVIDENCE {case_id: ev.case_id}]->(e)

// 2. BrowserVisit: one node per visit (provenance)
MERGE (v:BrowserVisit {event_id: ev.event_id})
SET v.timestamp    = ev.timestamp,
    v.url          = ev.url,
    v.title        = ev.title,
    v.severity     = ev.severity,
    v.anomaly_score = ev.anomaly_score,
    v.is_anomaly   = ev.is_anomaly,
    v.case_id      = ev.case_id,
    v.evidence_id  = ev.evidence_id,
    v.visit_count  = ev.visit_count
MERGE (e)-[:CONTAINS_VISIT {case_id: ev.case_id}]->(v)

// 3. Domain: deduped by case_id + domain_name (eliminates lock contention)
FOREACH (_ IN CASE WHEN ev.domain_id <> '' THEN [1] ELSE [] END |
    MERGE (d:Domain {domain_id: ev.domain_id})
    SET d.domain_name  = ev.domain_name,
        d.case_id      = ev.case_id
    MERGE (v)-[:VISITED_DOMAIN {case_id: ev.case_id, evidence_id: ev.evidence_id}]->(d)
)
"""

# ─── Generic/Sysmon/EVTX/PCAP Cypher ─────────────────────────────────────────
# Full entity model for non-browser sources. Unchanged from original.
_GENERIC_CYPHER = """
UNWIND $batch AS ev

// 1. Core Hierarchy: Case -> Evidence -> Event
MERGE (c:Case {case_id: ev.case_id})
MERGE (e:Evidence {evidence_id: ev.evidence_id})
SET e.case_id = ev.case_id
MERGE (c)-[:HAS_EVIDENCE {case_id: ev.case_id}]->(e)

MERGE (event:Event {event_id: ev.event_id})
SET event.timestamp     = ev.timestamp,
    event.event_type    = ev.event_type,
    event.source        = ev.source,
    event.severity      = ev.severity,
    event.anomaly_score = ev.anomaly_score,
    event.is_anomaly    = ev.is_anomaly,
    event.case_id       = ev.case_id,
    event.evidence_id   = ev.evidence_id

MERGE (e)-[:CONTAINS_EVENT {case_id: ev.case_id, evidence_id: ev.evidence_id}]->(event)

// 2. Entities: Host & User (only when explicitly set)
FOREACH (_ IN CASE WHEN ev.host_id <> '' AND ev.hostname <> 'DESKTOP-DEFAULT' THEN [1] ELSE [] END |
    MERGE (h:Host {host_id: ev.host_id})
    SET h.hostname = ev.hostname, h.case_id = ev.case_id
    MERGE (event)-[:OCCURRED_ON {case_id: ev.case_id, evidence_id: ev.evidence_id}]->(h)
)

FOREACH (_ IN CASE WHEN ev.user_id <> '' AND ev.username <> 'administrator' THEN [1] ELSE [] END |
    MERGE (u:User {user_id: ev.user_id})
    SET u.username = ev.username, u.domain = ev.domain, u.case_id = ev.case_id
    MERGE (event)-[:INVOLVES_USER {case_id: ev.case_id, evidence_id: ev.evidence_id}]->(u)
)

// 3. Process Entity
FOREACH (_ IN CASE WHEN ev.proc_id <> '' THEN [1] ELSE [] END |
    MERGE (p:Process {process_id: ev.proc_id})
    SET p.pid = ev.pid,
        p.process_name = ev.proc_name,
        p.command_line = ev.cmd_line,
        p.hash = ev.proc_hash,
        p.case_id = ev.case_id,
        p.host_id = ev.host_id

    MERGE (event)-[:INVOLVES_PROCESS {case_id: ev.case_id, evidence_id: ev.evidence_id}]->(p)
    FOREACH (__ IN CASE WHEN ev.user_id <> '' AND ev.username <> 'administrator' THEN [1] ELSE [] END |
        MERGE (u_proc:User {user_id: ev.user_id})
        MERGE (u_proc)-[:EXECUTED {case_id: ev.case_id, evidence_id: ev.evidence_id, timestamp: ev.timestamp}]->(p)
    )
)

// 4. Parent Process Spawn Relationship
FOREACH (_ IN CASE WHEN ev.parent_proc <> '' AND ev.proc_id <> '' THEN [1] ELSE [] END |
    MERGE (parent:Process {process_id: ev.case_id + ':' + ev.hostname + ':0:' + ev.parent_proc})
    SET parent.process_name = ev.parent_proc, parent.case_id = ev.case_id, parent.host_id = ev.host_id
    MERGE (p_child:Process {process_id: ev.proc_id})
    MERGE (parent)-[:SPAWNED {case_id: ev.case_id, evidence_id: ev.evidence_id, event_id: ev.event_id, timestamp: ev.timestamp, relationship_type: 'observed'}]->(p_child)
)

// 5. Network Connection
FOREACH (_ IN CASE WHEN ev.ip_id <> '' THEN [1] ELSE [] END |
    MERGE (ip:IPAddress {ip_id: ev.ip_id})
    SET ip.address = ev.dest_ip, ip.version = 'v4', ip.is_private = ev.is_private_ip, ip.case_id = ev.case_id

    FOREACH (__ IN CASE WHEN ev.proc_id <> '' THEN [1] ELSE [] END |
        MERGE (proc_net:Process {process_id: ev.proc_id})
        MERGE (proc_net)-[:CONNECTED_TO {case_id: ev.case_id, evidence_id: ev.evidence_id, event_id: ev.event_id, timestamp: ev.timestamp, relationship_type: 'observed'}]->(ip)
    )

    FOREACH (__ IN CASE WHEN ev.port_id <> '' THEN [1] ELSE [] END |
        MERGE (port:Port {port_id: ev.port_id})
        SET port.port_number = ev.dest_port, port.protocol = 'TCP', port.case_id = ev.case_id
        MERGE (ip)-[:USES_PORT {case_id: ev.case_id}]->(port)
    )
)

// 6. Domain Resolution
FOREACH (_ IN CASE WHEN ev.domain_id <> '' THEN [1] ELSE [] END |
    MERGE (d:Domain {domain_id: ev.domain_id})
    SET d.domain_name = ev.domain_name, d.case_id = ev.case_id
    FOREACH (__ IN CASE WHEN ev.proc_id <> '' THEN [1] ELSE [] END |
        MERGE (proc_dom:Process {process_id: ev.proc_id})
        MERGE (proc_dom)-[:RESOLVED {case_id: ev.case_id, evidence_id: ev.evidence_id, timestamp: ev.timestamp, relationship_type: 'observed'}]->(d)
    )
    FOREACH (__ IN CASE WHEN ev.ip_id <> '' THEN [1] ELSE [] END |
        MERGE (ip_dom:IPAddress {ip_id: ev.ip_id})
        MERGE (d)-[:RESOLVES_TO {case_id: ev.case_id}]->(ip_dom)
    )
)

// 7. Registry Modification
FOREACH (_ IN CASE WHEN ev.reg_id <> '' THEN [1] ELSE [] END |
    MERGE (r:RegistryKey {reg_id: ev.reg_id})
    SET r.path = ev.reg_path, r.case_id = ev.case_id
    FOREACH (__ IN CASE WHEN ev.proc_id <> '' THEN [1] ELSE [] END |
        MERGE (proc_reg:Process {process_id: ev.proc_id})
        MERGE (proc_reg)-[:MODIFIED_REGISTRY {case_id: ev.case_id, evidence_id: ev.evidence_id, timestamp: ev.timestamp, relationship_type: 'observed'}]->(r)
    )
)

// 8. File Activity
FOREACH (_ IN CASE WHEN ev.file_id <> '' THEN [1] ELSE [] END |
    MERGE (f:File {file_id: ev.file_id})
    SET f.filepath = ev.file_path, f.filename = ev.file_path, f.case_id = ev.case_id
    FOREACH (__ IN CASE WHEN ev.proc_id <> '' THEN [1] ELSE [] END |
        MERGE (proc_file:Process {process_id: ev.proc_id})
        MERGE (proc_file)-[:CREATED {case_id: ev.case_id, evidence_id: ev.evidence_id, timestamp: ev.timestamp, relationship_type: 'observed'}]->(f)
    )
)

// 9. Service Creation
FOREACH (_ IN CASE WHEN ev.svc_id <> '' THEN [1] ELSE [] END |
    MERGE (s:Service {service_id: ev.svc_id})
    SET s.service_name = ev.svc_name, s.case_id = ev.case_id
    FOREACH (__ IN CASE WHEN ev.proc_id <> '' THEN [1] ELSE [] END |
        MERGE (proc_svc:Process {process_id: ev.proc_id})
        MERGE (proc_svc)-[:CREATED_SERVICE {case_id: ev.case_id, evidence_id: ev.evidence_id, timestamp: ev.timestamp, relationship_type: 'observed'}]->(s)
    )
)
"""

CHUNK_SIZE = 500


def _extract_domain(url: str) -> str:
    """Extract registered domain from URL string."""
    try:
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        parsed = urlparse(url)
        host = parsed.hostname or ""
        # Strip leading www.
        return host.lstrip("www.") if host else ""
    except Exception:
        return ""


class GraphRepository:


    @classmethod
    async def delete_evidence_subgraph(cls, case_id: str, evidence_id: str) -> bool:
        """
        Safely purge Neo4j Event/BrowserVisit nodes and evidence-originated relationships
        for a specific case_id and evidence_id. Preserves shared cross-evidence domain entities.
        """
        driver = neo4j_service.get_driver()
        if not driver:
            return False
        try:
            async def _exec_delete(tx):
                # Delete Event nodes for this evidence_id within the case
                await tx.run(
                    "MATCH (e:Event {evidence_id: $ev_id, case_id: $case_id}) DETACH DELETE e",
                    ev_id=str(evidence_id), case_id=str(case_id)
                )
                # Delete BrowserVisit nodes for this evidence_id within the case
                await tx.run(
                    "MATCH (v:BrowserVisit {evidence_id: $ev_id, case_id: $case_id}) DETACH DELETE v",
                    ev_id=str(evidence_id), case_id=str(case_id)
                )
                # Delete Evidence node for this evidence_id within the case
                await tx.run(
                    "MATCH (ev:Evidence {evidence_id: $ev_id, case_id: $case_id}) DETACH DELETE ev",
                    ev_id=str(evidence_id), case_id=str(case_id)
                )

            async with driver.session(database=neo4j_service.database) as session:
                await session.execute_write(_exec_delete)
            return True
        except Exception as err:
            logger.warning(f"[GraphRepository] delete_evidence_subgraph error: {err}")
            return False

    @classmethod
    async def bulk_import_events(cls, events: List[Dict[str, Any]]) -> int:
        """
        Idempotently import normalized forensic events into Neo4j.

        Routes browser history events to a lightweight BrowserVisit+Domain schema
        (no fabricated Process/Host/User nodes) and other source types to the full
        entity model. This eliminates the lock-contention bottleneck that caused
        ~110s for 8,945 Chrome browser visits.

        Returns total events synced.
        """
        if not events:
            return 0

        driver = neo4j_service.get_driver()
        if not driver:
            logger.warning("[GraphRepository] Neo4j driver unavailable. Skipping graph sync.")
            return 0

        # Log the case_id that will be written to Neo4j (detect if it's ObjectId or str)
        first_cid_raw = events[0].get("case_id", "")
        first_cid = str(first_cid_raw)
        logger.info(
            f"[GraphRepository] bulk_import_events: {len(events)} events, "
            f"case_id type={type(first_cid_raw).__name__} value={first_cid} "
            f"source={events[0].get('source', 'unknown')}"
        )

        # ── Detect evidence source type ────────────────────────────────────────
        # Use first event's source field to determine routing
        sample_source = str(events[0].get("source", "")).lower()
        is_browser = sample_source == "browser"

        if is_browser:
            count = await cls._bulk_import_browser_events(events)
        else:
            count = await cls._bulk_import_generic_events(events)

        if count > 0:
            await cls.propagate_anomalies(first_cid)

        return count

    @classmethod
    async def _bulk_import_browser_events(cls, events: List[Dict[str, Any]]) -> int:
        """
        Browser-specific import: BrowserVisit + Domain schema.
        Avoids fabricating Process/Host/User nodes which caused lock contention.
        """
        driver = neo4j_service.get_driver()
        if not driver:
            return 0

        _t_prep = time.perf_counter()
        prepared = []
        for e in events:
            cid = str(e.get("case_id", ""))
            ev_id = str(e.get("evidence_id", ""))
            event_id = str(e.get("_id")) if "_id" in e else str(e.get("event_id", e.get("id", "")))
            if not event_id:
                continue

            ts = e["timestamp"].isoformat() if hasattr(e["timestamp"], "isoformat") else str(e.get("timestamp", ""))
            details = e.get("details", {}) or {}
            url = str(e.get("object", ""))
            domain_name = _extract_domain(url)
            domain_id = f"{cid}:{domain_name}" if domain_name else ""

            prepared.append({
                "case_id":      cid,
                "evidence_id":  ev_id,
                "event_id":     event_id,
                "timestamp":    ts,
                "url":          url,
                "title":        str(details.get("title", "")),
                "visit_count":  int(details.get("visit_count", 1)),
                "severity":     str(e.get("severity", "info")),
                "anomaly_score": float(e.get("anomaly_score", 0.0)),
                "is_anomaly":   bool(e.get("is_anomaly", False)),
                "domain_name":  domain_name,
                "domain_id":    domain_id,
            })

        prep_time = time.perf_counter() - _t_prep
        logger.info(f"[PROFILE] Neo4j browser preparation   {prep_time:.3f}s  ({len(prepared)} events)")

        total_synced = 0
        _t_write = time.perf_counter()
        try:
            for i in range(0, len(prepared), CHUNK_SIZE):
                chunk = prepared[i: i + CHUNK_SIZE]
                _t_batch = time.perf_counter()
                await neo4j_service.execute_query(_BROWSER_CYPHER, {"batch": chunk})
                total_synced += len(chunk)
                batch_num = i // CHUNK_SIZE + 1
                total_batches = (len(prepared) + CHUNK_SIZE - 1) // CHUNK_SIZE
                logger.info(
                    f"[NEO4J] Browser batch {batch_num}/{total_batches}: "
                    f"{len(chunk)} events  {time.perf_counter()-_t_batch:.2f}s"
                )
        except Exception as ex:
            logger.error(f"[GraphRepository] Browser bulk import failed: {ex}")

        write_time = time.perf_counter() - _t_write
        logger.info(f"[PROFILE] Neo4j browser writes         {write_time:.3f}s  ({total_synced} synced)")
        return total_synced

    @classmethod
    async def _bulk_import_generic_events(cls, events: List[Dict[str, Any]]) -> int:
        """
        Generic import for EVTX, PCAP, JSON, CSV, LOG etc.
        Creates the full entity model (Process, Host, User, IP, Domain, etc.)
        Only creates Host/User nodes when non-default values are present.
        """
        driver = neo4j_service.get_driver()
        if not driver:
            return 0

        _t_prep = time.perf_counter()
        prepared_events = []
        for e in events:
            cid = str(e.get("case_id", ""))
            ev_id = str(e.get("evidence_id", ""))
            event_id = str(e.get("_id")) if "_id" in e else str(e.get("event_id", e.get("id", "")))
            if not event_id:
                continue

            ts = e["timestamp"].isoformat() if hasattr(e["timestamp"], "isoformat") else str(e.get("timestamp", ""))
            details = e.get("details", {}) or {}

            # ── Safely unwrap nested dicts from PCAP/JSON parsers ─────────────
            # Parsers store structured fields as nested dicts: e["host"] = {"hostname":...}
            # Flat fields (EVTX/CSV/LOG) store them at top level: e["host"] = "DESKTOP-1"
            # Always extract primitives — never pass a dict as a Neo4j property value.
            raw_host = e.get("host", "")
            raw_network = e.get("network", {}) or {}
            raw_process = e.get("process", {}) or {}
            raw_user = e.get("user", {}) or {}
            raw_parent = e.get("parent_process", {}) or {}

            if isinstance(raw_host, dict):
                host_name = raw_host.get("hostname") or raw_host.get("ip") or ""
            else:
                host_name = str(raw_host) if raw_host else ""
            host_name = host_name or details.get("Computer") or details.get("Host") or "DESKTOP-DEFAULT"

            if isinstance(raw_user, dict):
                user_name = raw_user.get("username") or ""
                domain = raw_user.get("domain") or "WORKGROUP"
            else:
                user_name = str(raw_user) if raw_user else ""
                domain = details.get("TargetDomainName") or details.get("Domain") or "WORKGROUP"
            user_name = user_name or e.get("username") or details.get("TargetUserName") or details.get("User") or "administrator"

            if isinstance(raw_process, dict):
                proc_name = raw_process.get("name") or raw_process.get("path") or ""
                pid = raw_process.get("pid") or 0
                cmd_line = raw_process.get("command_line") or ""
                proc_hash = raw_process.get("hash") or ""
            else:
                proc_name = ""
                pid = e.get("pid") or details.get("ProcessId") or 0
                cmd_line = e.get("command_line") or details.get("CommandLine") or ""
                proc_hash = details.get("Hash") or details.get("SHA256") or ""
            proc_name = proc_name or e.get("process_name") or details.get("ProcessName") or e.get("subject", "process")

            if isinstance(raw_parent, dict):
                parent_proc = raw_parent.get("name") or ""
            else:
                parent_proc = str(raw_parent) if raw_parent else ""
            parent_proc = parent_proc or e.get("parent_process") or details.get("ParentProcessName") or ""
            # Guard: parent_proc must be a string
            if isinstance(parent_proc, dict):
                parent_proc = str(parent_proc.get("name", ""))

            if isinstance(raw_network, dict):
                dest_ip = raw_network.get("destination_ip") or raw_network.get("source_ip") or ""
                dest_port = raw_network.get("destination_port") or raw_network.get("source_port") or 0
                domain_name = raw_network.get("domain") or raw_network.get("dns_query") or ""
            else:
                dest_ip = e.get("destination_ip") or details.get("DestinationIP") or details.get("IpAddress") or ""
                dest_port = e.get("destination_port") or details.get("DestinationPort") or details.get("Port") or 0
                domain_name = details.get("DomainName") or details.get("QueryName") or ""

            # Ensure all string fields are actually strings (never dicts)
            def _safe_str(v) -> str:
                if v is None: return ""
                if isinstance(v, dict): return ""
                return str(v)

            host_name  = _safe_str(host_name)
            user_name  = _safe_str(user_name)
            domain     = _safe_str(domain)
            proc_name  = _safe_str(proc_name)
            parent_proc = _safe_str(parent_proc)
            dest_ip    = _safe_str(dest_ip)
            domain_name = _safe_str(domain_name)
            cmd_line   = _safe_str(cmd_line)
            proc_hash  = _safe_str(proc_hash)

            reg_path = details.get("ObjectName") if e.get("event_type") == "registry_change" else ""
            file_path = details.get("ObjectName") if e.get("event_type") in ("file_creation", "file_modification") else ""
            svc_name = details.get("ServiceName") or ""
            if isinstance(reg_path, dict):  reg_path = ""
            if isinstance(file_path, dict): file_path = ""
            if isinstance(svc_name, dict):  svc_name = ""
            reg_path  = _safe_str(reg_path)
            file_path = _safe_str(file_path)
            svc_name  = _safe_str(svc_name)

            host_id = f"{cid}:{host_name}" if host_name != "DESKTOP-DEFAULT" else ""
            user_id = f"{cid}:{domain}\\{user_name}" if user_name != "administrator" else ""

            # Sanitize pid and dest_port — must be int
            try:
                pid_int = int(pid) if pid and str(pid).isdigit() else 0
            except (TypeError, ValueError):
                pid_int = 0
            try:
                port_int = int(dest_port) if dest_port and str(dest_port).isdigit() else 0
            except (TypeError, ValueError):
                port_int = 0

            proc_id = f"{cid}:{host_name}:{pid_int}:{proc_name}" if proc_name and proc_name != "process" else ""
            ip_id = f"{cid}:{dest_ip}" if dest_ip else ""
            port_id = f"{cid}:{port_int}:TCP" if port_int else ""
            reg_id = f"{cid}:{reg_path}" if reg_path else ""
            file_id_val = file_path or details.get("SHA256") or details.get("FileName") or ""
            file_id = f"{cid}:{file_id_val}" if file_id_val else ""
            svc_id = f"{cid}:{host_name}:{svc_name}" if svc_name else ""
            domain_id = f"{cid}:{domain_name}" if domain_name else ""

            prepared_events.append({
                "case_id": cid,
                "evidence_id": ev_id,
                "event_id": event_id,
                "timestamp": ts,
                "event_type": str(e.get("event_type", "generic")),
                "source": str(e.get("source", "log")),
                "severity": str(e.get("severity", "info")),
                "anomaly_score": float(e.get("anomaly_score", 0.0)),
                "is_anomaly": bool(e.get("is_anomaly", False)),
                "action": str(e.get("action", "occurred")),
                "host_id": host_id,
                "hostname": host_name,
                "user_id": user_id,
                "username": user_name,
                "domain": domain,
                "proc_id": proc_id,
                "pid": pid_int,
                "proc_name": proc_name,
                "cmd_line": cmd_line,
                "proc_hash": proc_hash,
                "parent_proc": parent_proc,
                "dest_ip": dest_ip,
                "ip_id": ip_id,
                "is_private_ip": cls._is_private_ip(dest_ip) if dest_ip else False,
                "dest_port": port_int,
                "port_id": port_id,
                "domain_name": domain_name,
                "domain_id": domain_id,
                "reg_path": reg_path,
                "reg_id": reg_id,
                "file_path": file_path,
                "file_id": file_id,
                "svc_name": svc_name,
                "svc_id": svc_id,
            })

        prep_time = time.perf_counter() - _t_prep
        logger.info(f"[PROFILE] Neo4j generic preparation   {prep_time:.3f}s  ({len(prepared_events)} events)")

        total_synced = 0
        _t_write = time.perf_counter()
        try:
            for i in range(0, len(prepared_events), CHUNK_SIZE):
                chunk = prepared_events[i: i + CHUNK_SIZE]
                _t_batch = time.perf_counter()
                await neo4j_service.execute_query(_GENERIC_CYPHER, {"batch": chunk})
                total_synced += len(chunk)
                batch_num = i // CHUNK_SIZE + 1
                total_batches = (len(prepared_events) + CHUNK_SIZE - 1) // CHUNK_SIZE
                logger.info(
                    f"[NEO4J] Generic batch {batch_num}/{total_batches}: "
                    f"{len(chunk)} events  {time.perf_counter()-_t_batch:.2f}s"
                )
        except Exception as ex:
            logger.error(f"[GraphRepository] Generic bulk import failed: {ex}")

        write_time = time.perf_counter() - _t_write
        logger.info(f"[PROFILE] Neo4j generic writes         {write_time:.3f}s  ({total_synced} synced)")
        return total_synced

    @classmethod
    async def update_anomaly_scores(cls, anomaly_updates: List[Dict[str, Any]]) -> None:
        """
        Batch-update anomaly scores on Event AND BrowserVisit nodes via UNWIND.
        Single query per call — not one query per event.
        """
        if not anomaly_updates:
            return

        _t = time.perf_counter()

        # Update Event nodes (EVTX, PCAP, etc.)
        event_cypher = """
        UNWIND $batch AS item
        MATCH (ev:Event {event_id: item.event_id})
        SET ev.is_anomaly = item.is_anomaly,
            ev.anomaly_score = item.anomaly_score
        """
        # Update BrowserVisit nodes
        visit_cypher = """
        UNWIND $batch AS item
        MATCH (v:BrowserVisit {event_id: item.event_id})
        SET v.is_anomaly = item.is_anomaly,
            v.anomaly_score = item.anomaly_score
        """
        # Also propagate anomaly status to connected entities and relationships
        entity_cypher = """
        UNWIND $batch AS item
        MATCH (ev {event_id: item.event_id})-[r]-(ent)
        WHERE item.is_anomaly = true OR item.anomaly_score > 0.5
        SET ent.is_anomaly = true,
            ent.anomaly_score = case when item.anomaly_score > coalesce(ent.anomaly_score, 0.0) then item.anomaly_score else ent.anomaly_score end,
            r.is_anomaly = true,
            r.anomaly_score = case when item.anomaly_score > coalesce(r.anomaly_score, 0.0) then item.anomaly_score else r.anomaly_score end
        """
        try:
            await neo4j_service.execute_query(event_cypher, {"batch": anomaly_updates})
            await neo4j_service.execute_query(visit_cypher, {"batch": anomaly_updates})
            await neo4j_service.execute_query(entity_cypher, {"batch": anomaly_updates})
            elapsed = time.perf_counter() - _t
            logger.info(
                f"[PROFILE] Neo4j anomaly score sync     {elapsed:.3f}s  "
                f"({len(anomaly_updates)} updates)"
            )
        except Exception as e:
            logger.warning(f"[GraphRepository] Anomaly score update failed: {e}")

    @classmethod
    async def propagate_anomalies(cls, case_id: str) -> None:
        """
        Propagate anomaly status from Event/BrowserVisit nodes to connected entity nodes & relationships.
        """
        driver = neo4j_service.get_driver()
        if not driver:
            return
        prop_cypher = """
        MATCH (ev {case_id: $case_id})-[r]-(ent)
        WHERE (ev:Event OR ev:BrowserVisit) AND (ev.is_anomaly = true OR ev.anomaly_score > 0.5)
        SET ent.is_anomaly = true,
            ent.anomaly_score = case when ev.anomaly_score > coalesce(ent.anomaly_score, 0.0) then ev.anomaly_score else ent.anomaly_score end,
            r.is_anomaly = true,
            r.anomaly_score = case when ev.anomaly_score > coalesce(r.anomaly_score, 0.0) then ev.anomaly_score else r.anomaly_score end
        """
        try:
            await neo4j_service.execute_query(prop_cypher, {"case_id": str(case_id)})
        except Exception as e:
            logger.warning(f"[GraphRepository] propagate_anomalies error: {e}")

    @staticmethod
    def _is_private_ip(ip: str) -> bool:
        """Return True if IP is in RFC1918 private ranges."""
        try:
            parts = ip.split(".")
            if len(parts) != 4:
                return False
            a, b = int(parts[0]), int(parts[1])
            return (
                a == 10
                or (a == 172 and 16 <= b <= 31)
                or (a == 192 and b == 168)
                or a == 127
            )
        except Exception:
            return False

    @staticmethod
    def _safe_props(obj) -> dict:
        """Safely convert a Neo4j Node/Relationship or dict-like object to a plain dict."""
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, '_properties'):
            return dict(obj._properties)
        if hasattr(obj, 'items'):
            try:
                return dict(obj.items())
            except Exception:
                return {}
        if hasattr(obj, 'keys'):
            try:
                keys = obj.keys()
                return {k: obj[k] for k in keys}
            except Exception:
                return {}
        if not isinstance(obj, str):
            try:
                return dict(obj)
            except (TypeError, ValueError):
                return {}
        return {}

    @classmethod
    async def get_case_graph(
        cls,
        case_id: str,
        org_id: str,
        evidence_id: Optional[str] = None,
        limit: int = 1000,
        anomaly_only: bool = False,
    ) -> Dict[str, List[Any]]:
        """
        Retrieve application-level stable JSON graph nodes and edges for Cytoscape.
        Supports both the legacy Event schema and the new BrowserVisit+Domain schema.

        Filtering strategy:
        - Primary: match any relationship OR node that carries case_id = $case_id.
          This covers cases where case_id is stored on the relationship (r.case_id)
          OR on the source/target node (s.case_id / t.case_id) so shared domain
          nodes (IPAddress, Domain) that don't have case_id on every rel are included.
        """
        driver = neo4j_service.get_driver()
        if not driver:
            logger.warning("[GraphRepository] Neo4j driver unavailable for graph fetch.")
            return {"nodes": [], "edges": []}

        params: Dict[str, Any] = {"case_id": case_id, "limit": limit}

        # Use OR across node and relationship case_id so we catch all graph data
        case_filter = "(r.case_id = $case_id OR s.case_id = $case_id OR t.case_id = $case_id)"
        extra_clauses = []

        if evidence_id:
            extra_clauses.append(
                "(r.evidence_id = $evidence_id OR s.evidence_id = $evidence_id OR t.evidence_id = $evidence_id OR EXISTS { MATCH (ev_scope:Evidence {evidence_id: $evidence_id, case_id: $case_id})-[*1..3]-(s) } OR EXISTS { MATCH (ev_scope:Evidence {evidence_id: $evidence_id, case_id: $case_id})-[*1..3]-(t) })"
            )
            params["evidence_id"] = evidence_id
        if anomaly_only:
            extra_clauses.append(
                "(r.is_anomaly = true OR r.anomaly_score > 0.5 OR s.is_anomaly = true OR s.anomaly_score > 0.5 OR t.is_anomaly = true OR t.anomaly_score > 0.5 OR EXISTS { MATCH (s)-(ev_anom) WHERE (ev_anom.is_anomaly = true OR ev_anom.anomaly_score > 0.5) } OR EXISTS { MATCH (t)-(ev_anom) WHERE (ev_anom.is_anomaly = true OR ev_anom.anomaly_score > 0.5) })"
            )

        where_parts = [case_filter] + extra_clauses
        where_str = "WHERE " + " AND ".join(where_parts)

        cypher = f"""
        MATCH (s)-[r]->(t)
        {where_str}
        RETURN
            labels(s)[0] AS source_type,
            coalesce(s.process_id, s.user_id, s.host_id, s.ip_id, s.address,
                     s.domain_id, s.domain_name, s.reg_id, s.file_id, s.path,
                     s.event_id, s.evidence_id, s.case_id, s.service_id, s.port_id) AS source_id,
            coalesce(s.process_name, s.username, s.hostname, s.address,
                     s.domain_name, s.url, s.filename, s.path, s.event_type,
                     s.case_id) AS source_label,
            s AS source_props,

            type(r) AS rel_type,
            r AS rel_props,

            labels(t)[0] AS target_type,
            coalesce(t.process_id, t.user_id, t.host_id, t.ip_id, t.address,
                     t.domain_id, t.domain_name, t.reg_id, t.file_id, t.path,
                     t.event_id, t.evidence_id, t.case_id, t.service_id, t.port_id) AS target_id,
            coalesce(t.process_name, t.username, t.hostname, t.address,
                     t.domain_name, t.url, t.filename, t.path, t.event_type,
                     t.case_id) AS target_label,
            t AS target_props
        LIMIT $limit
        """

        try:
            records = await neo4j_service.execute_query(cypher, params)
            logger.info(
                f"[GraphRepository] get_case_graph "
                f"case_id={case_id!r} evidence_id={evidence_id!r} "
                f"limit={limit} → {len(records)} rows from Neo4j"
            )
            if len(records) == 0:
                # Diagnostic: check if any nodes exist for this case_id
                diag = await neo4j_service.execute_query(
                    "MATCH (n) WHERE n.case_id = $cid RETURN count(n) AS cnt",
                    {"cid": case_id}
                )
                node_cnt = diag[0]["cnt"] if diag else 0
                if node_cnt > 0:
                    logger.warning(
                        f"[GraphRepository] {node_cnt} nodes exist for case_id={case_id} "
                        f"but graph MATCH (s)-[r]->(t) WHERE ... returned 0 rows. "
                        f"All nodes may be isolated (no relationships). "
                        f"Evidence nodes with no events will not appear in graph."
                    )
                else:
                    # Check what case_ids ARE in Neo4j
                    existing = await neo4j_service.execute_query(
                        "MATCH (n) WHERE n.case_id IS NOT NULL "
                        "RETURN DISTINCT n.case_id AS cid LIMIT 10"
                    )
                    stored = [r["cid"] for r in existing]
                    logger.warning(
                        f"[GraphRepository] ZERO nodes in Neo4j for case_id={case_id!r}. "
                        f"Neo4j has data for these case_ids: {stored}. "
                        f"This is a case_id mismatch — pipeline may have written data under a different id. "
                        f"Use POST /cases/{case_id}/graph/sync to re-sync from MongoDB."
                    )
            nodes_dict: Dict[str, Any] = {}
            edges = []

            for row in records:
                s_id = str(row["source_id"] or "")
                s_type = str(row["source_type"] or "GenericEntity")
                s_label = str(row["source_label"] or s_id)
                s_props = cls._safe_props(row.get("source_props"))

                t_id = str(row["target_id"] or "")
                t_type = str(row["target_type"] or "GenericEntity")
                t_label = str(row["target_label"] or t_id)
                t_props = cls._safe_props(row.get("target_props"))

                if s_id and s_id not in nodes_dict:
                    nodes_dict[s_id] = {
                        "id": f"{s_type.lower()}:{s_id}",
                        "raw_id": s_id,
                        "type": s_type,
                        "label": s_label,
                        "properties": s_props,
                    }

                if t_id and t_id not in nodes_dict:
                    nodes_dict[t_id] = {
                        "id": f"{t_type.lower()}:{t_id}",
                        "raw_id": t_id,
                        "type": t_type,
                        "label": t_label,
                        "properties": t_props,
                    }

                rel_props = cls._safe_props(row.get("rel_props"))

                # Skip edges where source or target id could not be resolved
                if not s_id or not t_id:
                    continue

                edges.append({
                    "id": f"edge-{len(edges)+1}",
                    "source": f"{s_type.lower()}:{s_id}",
                    "target": f"{t_type.lower()}:{t_id}",
                    "type": row["rel_type"],
                    "action": rel_props.get("action", row["rel_type"]),
                    "properties": rel_props,
                    "evidence_id": rel_props.get("evidence_id", ""),
                    "is_anomaly": bool(
                        rel_props.get("is_anomaly", False)
                        or s_props.get("is_anomaly", False)
                        or t_props.get("is_anomaly", False)
                    ),
                })

            logger.info(
                f"[GraphRepository] Graph built: {len(nodes_dict)} nodes, {len(edges)} edges "
                f"for case={case_id}"
            )
            return {"nodes": list(nodes_dict.values()), "edges": edges}

        except Exception as e:
            logger.error(f"[GraphRepository] Error fetching case graph for case={case_id}: {e}")
            return {"nodes": [], "edges": []}

    @classmethod
    async def clear_case_graph(cls, case_id: str, org_id: str) -> None:
        """Detach and delete all nodes associated with a case."""
        cypher = """
        MATCH (n)
        WHERE n.case_id = $case_id
        DETACH DELETE n
        """
        try:
            await neo4j_service.execute_query(cypher, {"case_id": case_id})
            logger.info(f"[GraphRepository] Cleared Neo4j nodes for case {case_id}")
        except Exception as e:
            logger.error(f"[GraphRepository] Failed clearing case graph: {e}")
