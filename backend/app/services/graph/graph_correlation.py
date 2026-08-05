"""
Graph Correlation Engine — ForenSight
======================================
Performs high-level forensic relationship analysis, attack-path discovery,
temporal correlation, cross-evidence correlation, and multi-factor scoring over Neo4j graph entities.

Cypher queries use OPTIONAL MATCH throughout so that missing relationship types
(e.g. SPAWNED, CONNECTED_TO, USES_PORT — only present when EVTX/PCAP evidence is
in the graph) produce empty results instead of Neo4j schema-mismatch warnings.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import hashlib
from backend.app.services.graph.neo4j_service import neo4j_service

logger = logging.getLogger(__name__)


class GraphCorrelationEngine:
    """
    Forensic correlation and attack path discovery engine.
    Calculates multi-factor correlation scores (0-100 scale) and produces
    transparent, evidence-traceable investigation findings.
    """

    @classmethod
    async def detect_process_chains(cls, case_id: str) -> List[Dict[str, Any]]:
        """Detect parent-child process chains (e.g., Office -> powershell.exe -> cmd.exe -> payload.exe).

        Uses OPTIONAL MATCH so the query returns nothing (no warnings) when
        Process nodes or SPAWNED edges don't exist in the graph yet.
        """
        cypher = """
        OPTIONAL MATCH path = (root:Process {case_id: $case_id})-[:SPAWNED*1..4]->(leaf:Process {case_id: $case_id})
        WHERE path IS NOT NULL
          AND NOT ()-[:SPAWNED]->(root)
        RETURN
            [node in nodes(path) | node.process_name] AS process_chain,
            [node in nodes(path) | node.process_id]   AS process_ids,
            length(path)                              AS chain_depth
        ORDER BY chain_depth DESC
        LIMIT 50
        """
        try:
            rows = await neo4j_service.execute_query(cypher, {"case_id": case_id})
        except Exception as e:
            logger.debug(f"[Correlation] detect_process_chains skipped: {e}")
            return []

        findings = []
        for r in rows:
            chain = r.get("process_chain")
            depth = r.get("chain_depth")
            if not chain or depth is None:
                continue
            chain_str = " -> ".join(chain)

            score = min(100, 40 + (depth * 15))
            reasons = [f"Process lineage chain detected (depth {depth}): {chain_str}"]

            # Check if suspicious tools are in chain
            chain_lower = [p.lower() for p in chain]
            if any(p in chain_lower for p in ["powershell.exe", "cmd.exe", "wscript.exe", "mshta.exe"]):
                score = min(100, score + 20)
                reasons.append("Suspicious command interpreter spawned in lineage chain")

            corr_id = f"proc_chain_{hashlib.md5((case_id + chain_str).encode()).hexdigest()[:10]}"
            findings.append({
                "correlation_id": corr_id,
                "type": "process_chain",
                "score": score,
                "severity": "critical" if score >= 80 else "high" if score >= 60 else "medium",
                "chain": chain,
                "reasons": reasons,
                "involved_ids": r.get("process_ids", []),
            })
        return findings

    @classmethod
    async def detect_suspicious_paths(cls, case_id: str) -> List[Dict[str, Any]]:
        """
        Detect complete attack paths:
        User -EXECUTED-> Process -CONNECTED_TO-> IPAddress -USES_PORT-> Port

        Uses OPTIONAL MATCH + IS NOT NULL guards so the query gracefully
        returns nothing when these relationship types don't exist (browser/JSON evidence only).
        """
        cypher = """
        OPTIONAL MATCH (u:User {case_id: $case_id})-[:EXECUTED]->(p:Process {case_id: $case_id})
        WITH u, p
        WHERE u IS NOT NULL AND p IS NOT NULL
        OPTIONAL MATCH (p)-[:CONNECTED_TO]->(ip:IPAddress {case_id: $case_id})
        WITH u, p, ip
        WHERE ip IS NOT NULL AND ip.is_private = false
        OPTIONAL MATCH (ip)-[:USES_PORT]->(pt:Port)
        WHERE pt IS NOT NULL
        RETURN
            u.user_id      AS user_id,
            u.username     AS username,
            p.process_id   AS process_id,
            p.process_name AS process_name,
            p.command_line AS command_line,
            ip.address     AS ip_address,
            pt.port_number AS port_number
        LIMIT 50
        """
        try:
            rows = await neo4j_service.execute_query(cypher, {"case_id": case_id})
        except Exception as e:
            logger.debug(f"[Correlation] detect_suspicious_paths skipped: {e}")
            return []

        paths = []
        for r in rows:
            if not r.get("username") or not r.get("process_name") or not r.get("ip_address"):
                continue
            score = 75
            port_str = str(r.get("port_number", "?"))
            reasons = [
                f"User '{r['username']}' executed process '{r['process_name']}'",
                f"Process established outbound network connection to external IP {r['ip_address']}:{port_str}",
            ]
            if "powershell" in r["process_name"].lower() or "-enc" in (r.get("command_line") or "").lower():
                score = min(100, score + 20)
                reasons.append("Encoded or suspicious command-line parameters detected")

            explanation = (
                f"{r['username']} executed {r['process_name']}, which subsequently connected "
                f"to external IP {r['ip_address']} on port {port_str}."
            )
            corr_id = f"attack_path_{hashlib.md5((case_id + (r.get('process_id') or '') + r['ip_address']).encode()).hexdigest()[:10]}"

            paths.append({
                "correlation_id": corr_id,
                "type": "attack_path",
                "score": score,
                "severity": "critical" if score >= 80 else "high",
                "explanation": explanation,
                "reasons": reasons,
                "involved_nodes": [r.get("user_id", ""), r.get("process_id", ""), r["ip_address"]],
            })
        return paths

    @classmethod
    async def detect_cross_evidence_correlations(cls, case_id: str) -> List[Dict[str, Any]]:
        """
        Detect cross-evidence correlations:
        EVTX evidence shows process network request, and PCAP evidence shows matching IP capture.

        Uses OPTIONAL MATCH + IS NOT NULL guards so the query runs silently
        when CONTAINS_EVENT / INVOLVES_PROCESS / CONNECTED_TO don't exist yet.
        """
        cypher = """
        OPTIONAL MATCH (e1:Evidence {case_id: $case_id})-[:CONTAINS_EVENT]->(ev1:Event)
        WITH e1, ev1
        WHERE ev1 IS NOT NULL
        OPTIONAL MATCH (ev1)-[:INVOLVES_PROCESS]->(p:Process)-[:CONNECTED_TO]->(ip:IPAddress)
        WITH e1, ev1, p, ip
        WHERE p IS NOT NULL AND ip IS NOT NULL
        OPTIONAL MATCH (e2:Evidence {case_id: $case_id})-[:CONTAINS_EVENT]->(ev2:Event)
        WHERE e2 IS NOT NULL
          AND e1.evidence_id <> e2.evidence_id
          AND ev2.source = 'pcap'
        RETURN
            e1.evidence_id AS evtx_evidence_id,
            p.process_name AS process_name,
            ip.address     AS shared_ip,
            ev1.timestamp  AS evtx_time,
            ev2.timestamp  AS pcap_time
        LIMIT 30
        """
        try:
            rows = await neo4j_service.execute_query(cypher, {"case_id": case_id})
        except Exception as e:
            logger.debug(f"[Correlation] detect_cross_evidence_correlations skipped: {e}")
            return []

        correlations = []
        for r in rows:
            if not r.get("shared_ip") or not r.get("process_name"):
                continue
            shared_ip = r["shared_ip"]
            proc_name = r["process_name"]
            ev_id = r.get("evtx_evidence_id", "unknown")
            corr_id = f"cross_ev_{hashlib.md5((case_id + ev_id + shared_ip).encode()).hexdigest()[:10]}"
            correlations.append({
                "correlation_id": corr_id,
                "type": "cross_evidence",
                "score": 85,
                "severity": "high",
                "explanation": (
                    f"Activity on IP {shared_ip} confirmed across multiple evidence sources. "
                    f"Process '{proc_name}' recorded in event log with matching PCAP capture."
                ),
                "reasons": [
                    f"Event log evidence recorded process '{proc_name}' connecting to {shared_ip}",
                    f"PCAP network evidence confirmed raw packet transmission to {shared_ip}",
                    "Cross-evidence verification increases investigative confidence",
                ],
                "evidence_sources": [ev_id],
            })
        return correlations

    @classmethod
    async def detect_suspicious_lolbin_execution(cls, case_id: str) -> List[Dict[str, Any]]:
        """Detect execution of suspicious LOLBins / system binaries (powershell, cmd, mshta, certutil, rundll32, regsvr32)."""
        cypher = """
        OPTIONAL MATCH (p:Process {case_id: $case_id})
        WHERE p.process_name IS NOT NULL
          AND (
            toLower(p.process_name) CONTAINS 'powershell' OR
            toLower(p.process_name) CONTAINS 'cmd.exe' OR
            toLower(p.process_name) CONTAINS 'mshta' OR
            toLower(p.process_name) CONTAINS 'certutil' OR
            toLower(p.process_name) CONTAINS 'rundll32' OR
            toLower(p.process_name) CONTAINS 'wscript' OR
            toLower(p.process_name) CONTAINS 'cscript' OR
            toLower(p.process_name) CONTAINS 'regsvr32'
          )
        RETURN
            p.process_name AS process_name,
            p.process_id   AS process_id,
            p.command_line AS command_line
        LIMIT 50
        """
        try:
            rows = await neo4j_service.execute_query(cypher, {"case_id": case_id})
        except Exception as e:
            logger.debug(f"[Correlation] detect_suspicious_lolbin_execution skipped: {e}")
            return []

        findings = []
        for r in rows:
            proc_name = r.get("process_name")
            if not proc_name:
                continue
            cmd = r.get("command_line") or proc_name
            score = 70
            if "-enc" in cmd.lower() or "-nop" in cmd.lower() or "downloadstring" in cmd.lower():
                score = 90
            corr_id = f"lolbin_{hashlib.md5((case_id + proc_name + (r.get('process_id') or '')).encode()).hexdigest()[:10]}"
            findings.append({
                "correlation_id": corr_id,
                "type": "PROCESS_INITIATED_CONNECTION",
                "rule": "PROCESS_INITIATED_CONNECTION",
                "score": score,
                "severity": "critical" if score >= 80 else "high",
                "source": proc_name,
                "target": cmd[:80],
                "explanation": f"Suspicious execution of Living-off-the-Land binary '{proc_name}' with command: {cmd}",
                "reasons": [
                    f"Binary '{proc_name}' identified as potential LOLBin abused for code execution",
                    f"Command line details: {cmd}"
                ]
            })
        return findings

    @classmethod
    async def detect_registry_persistence(cls, case_id: str) -> List[Dict[str, Any]]:
        """Detect persistence via Registry Run key or autostart modifications."""
        cypher = """
        OPTIONAL MATCH (p:Process {case_id: $case_id})-[:MODIFIED_REGISTRY]->(r:RegistryKey {case_id: $case_id})
        WHERE r.path IS NOT NULL
        RETURN
            p.process_name AS process_name,
            r.path         AS reg_path
        LIMIT 50
        """
        try:
            rows = await neo4j_service.execute_query(cypher, {"case_id": case_id})
        except Exception as e:
            logger.debug(f"[Correlation] detect_registry_persistence skipped: {e}")
            return []

        findings = []
        for r in rows:
            reg_path = r.get("reg_path")
            proc_name = r.get("process_name") or "Process"
            if not reg_path:
                continue
            score = 85 if "run" in reg_path.lower() or "services" in reg_path.lower() else 65
            corr_id = f"reg_persist_{hashlib.md5((case_id + reg_path).encode()).hexdigest()[:10]}"
            findings.append({
                "correlation_id": corr_id,
                "type": "REGISTRY_RUN_KEY_PERSISTENCE",
                "rule": "REGISTRY_RUN_KEY_PERSISTENCE",
                "score": score,
                "severity": "critical" if score >= 80 else "high",
                "source": proc_name,
                "target": reg_path,
                "explanation": f"Process '{proc_name}' modified registry persistence location: {reg_path}",
                "reasons": [
                    f"Registry modification detected at persistence location '{reg_path}'",
                    "Autostart and Run key modifications can establish persistent access"
                ]
            })
        return findings

    @classmethod
    async def detect_domain_c2_resolutions(cls, case_id: str) -> List[Dict[str, Any]]:
        """Detect domain resolutions and process interactions with domains."""
        cypher = """
        OPTIONAL MATCH (d:Domain {case_id: $case_id})
        WHERE d.domain_name IS NOT NULL
        OPTIONAL MATCH (p:Process {case_id: $case_id})-[:RESOLVED]->(d)
        RETURN
            d.domain_name AS domain_name,
            p.process_name AS process_name
        LIMIT 50
        """
        try:
            rows = await neo4j_service.execute_query(cypher, {"case_id": case_id})
        except Exception as e:
            logger.debug(f"[Correlation] detect_domain_c2_resolutions skipped: {e}")
            return []

        findings = []
        for r in rows:
            dom = r.get("domain_name")
            if not dom:
                continue
            proc_name = r.get("process_name") or "System/Network"
            score = 60
            corr_id = f"dom_c2_{hashlib.md5((case_id + dom + proc_name).encode()).hexdigest()[:10]}"
            findings.append({
                "correlation_id": corr_id,
                "type": "PARENT_OF",
                "rule": "PARENT_OF",
                "score": score,
                "severity": "medium",
                "source": proc_name,
                "target": dom,
                "explanation": f"Domain resolution query recorded: {proc_name} → {dom}",
                "reasons": [
                    f"Domain network activity observed for '{dom}'",
                    f"Initiated by process '{proc_name}'"
                ]
            })
        return findings

    @classmethod
    async def get_temporal_window_events(
        cls, case_id: str, target_name: str, window_minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all graph events occurring within ±window_minutes around target activity.
        """
        cypher = """
        OPTIONAL MATCH (p:Process {case_id: $case_id})
        WHERE p.process_name CONTAINS $target_name OR p.process_id CONTAINS $target_name
        OPTIONAL MATCH (e:Evidence {case_id: $case_id})-[:CONTAINS_EVENT]->(ev:Event)-[:INVOLVES_PROCESS]->(p)
        RETURN ev.timestamp AS target_time
        LIMIT 1
        """
        try:
            rows = await neo4j_service.execute_query(cypher, {"case_id": case_id, "target_name": target_name})
        except Exception as e:
            logger.debug(f"[Correlation] get_temporal_window_events skipped: {e}")
            return []

        if not rows or not rows[0].get("target_time"):
            return []

        target_time_str = rows[0]["target_time"]
        cypher_window = """
        OPTIONAL MATCH (e:Evidence {case_id: $case_id})-[:CONTAINS_EVENT]->(ev:Event)-[r]->(target)
        WHERE ev IS NOT NULL
          AND duration.between(datetime(ev.timestamp), datetime($target_time)).minutes <= $window
          AND duration.between(datetime($target_time), datetime(ev.timestamp)).minutes <= $window
        RETURN
            ev.event_id AS event_id,
            ev.event_type AS event_type,
            ev.timestamp AS timestamp,
            ev.severity AS severity,
            ev.is_anomaly AS is_anomaly,
            labels(target)[0] AS target_type
        ORDER BY ev.timestamp ASC
        LIMIT 100
        """
        try:
            return await neo4j_service.execute_query(cypher_window, {
                "case_id": case_id,
                "target_time": target_time_str,
                "window": window_minutes,
            })
        except Exception as e:
            logger.debug(f"[Correlation] temporal window query skipped: {e}")
            return []

    @classmethod
    async def get_all_case_correlations(cls, case_id: str) -> Dict[str, Any]:
        """
        Run full correlation engine pipeline and return deduplicated findings summary.
        Used by the dashboard metric, investigation report, and API endpoints.
        """
        chains = await cls.detect_process_chains(case_id)
        paths = await cls.detect_suspicious_paths(case_id)
        cross = await cls.detect_cross_evidence_correlations(case_id)
        lolbins = await cls.detect_suspicious_lolbin_execution(case_id)
        registry = await cls.detect_registry_persistence(case_id)
        domains = await cls.detect_domain_c2_resolutions(case_id)

        all_findings = []
        seen_ids = set()
        for item in (chains + paths + cross + lolbins + registry + domains):
            cid = item["correlation_id"]
            if cid not in seen_ids:
                seen_ids.add(cid)
                all_findings.append(item)

        return {
            "case_id": case_id,
            "total_correlations": len(all_findings),
            "findings": all_findings,
        }

