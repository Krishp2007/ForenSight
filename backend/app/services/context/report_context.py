"""
Report Context Builder — ForenSight AI
=========================================
Assembles all context pieces needed to render the full HTML/PDF report.
Feeds into ReportCompiler so the Jinja2 template has rich, structured data.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from backend.app.repositories.case_repository import CaseRepository
from backend.app.repositories.graph_repository import GraphRepository
from backend.app.knowledge.mitre_mapper import MitreMapper
from backend.app.services.context.anomaly_context import build_anomaly_context
from backend.app.services.context.graph_context import build_graph_context
from backend.app.services.context.timeline_context import build_timeline_context
from backend.app.db.mongodb import db_client

logger = logging.getLogger(__name__)


def _get_plain_description(ev: dict) -> str:
    if ev.get("description"):
        return ev["description"]
    subj = ev.get("subject", "System")
    act = str(ev.get("action", "activity")).replace("_", " ")
    obj = ev.get("object", "event")
    source = str(ev.get("source") or "").lower()
    ev_type = str(ev.get("event_type") or "").lower()
    details = ev.get("details") or {}

    if source == "pcap" or "network" in ev_type:
        proto_code = details.get("proto_code")
        proto = "TCP" if proto_code == 6 else "UDP" if proto_code == 17 else "IP"
        length = f" ({details.get('length')} bytes)" if details.get("length") else ""
        dport = f" on port {details.get('dport')}" if details.get("dport") else ""
        return f"Host {subj} transmitted a {proto} packet{length} to destination {obj}{dport}."

    if "browser" in ev_type:
        title = details.get("title")
        if title:
            return f"User visited '{title}' via {subj}."
        return f"User visited web link via {subj}."

    if "process" in ev_type:
        cmd = f" running command '{details.get('command_line')}'" if details.get("command_line") else ""
        return f"Process {subj} executed child process {obj}{cmd}."

    if "auth" in ev_type:
        return f"User {subj} performed {act} on target {obj}."

    return f"{subj} {act} {obj}"


async def build_report_context(case_id: str, org_id: str) -> Dict[str, Any]:
    """
    Gather all structured data required by the report Jinja2 template.
    """
    case = await CaseRepository.get_by_id(case_id, org_id)
    if not case:
        raise ValueError(f"Case {case_id} not found for org {org_id}")

    from backend.app.repositories.evidence_repository import EvidenceRepository

    # Parallel fetch where possible with exception safety
    import asyncio
    results = await asyncio.gather(
        build_anomaly_context(case, limit=100),
        build_graph_context(case_id, org_id),
        GraphRepository.get_case_graph(case_id, org_id),
        build_timeline_context(case, limit=500),
        EvidenceRepository.list_by_case(case_id, org_id),
        return_exceptions=True,
    )
    anomalies = results[0] if not isinstance(results[0], Exception) else []
    if isinstance(results[0], Exception):
        logger.error(f"build_anomaly_context error: {results[0]}")

    correlations = results[1] if not isinstance(results[1], Exception) else []
    if isinstance(results[1], Exception):
        logger.error(f"build_graph_context error: {results[1]}")

    graph = results[2] if not isinstance(results[2], Exception) else {"nodes": [], "edges": []}
    if isinstance(results[2], Exception):
        logger.error(f"get_case_graph error: {results[2]}")

    timeline_ctx = results[3] if not isinstance(results[3], Exception) else {"events": [], "sessions": [], "total": 0, "span_hours": 0}
    if isinstance(results[3], Exception):
        logger.error(f"build_timeline_context error: {results[3]}")

    evidence_list = results[4] if not isinstance(results[4], Exception) else []
    if isinstance(results[4], Exception):
        logger.error(f"EvidenceRepository.list_by_case error: {results[4]}")

    # Aggregate counts via EventRepository to match Dashboard stats exactly
    from backend.app.repositories.event_repository import EventRepository
    stats_data = await EventRepository.count_case_stats(case_id, org_id)
    total_events = stats_data["total"]
    anomalies_count = stats_data["anomalies"]
    critical_high_count = stats_data["critical"]

    # Attach plain English descriptions to anomalies (top 10 max for report)
    anomalies_top = anomalies[:10]
    for a in anomalies_top:
        a["description"] = _get_plain_description(a)
        ts = a.get("timestamp")
        if isinstance(ts, datetime):
            a["timestamp"] = ts.strftime("%Y-%m-%d %H:%M:%S")

    # Select top 12 Key Incident Milestones for the summary timeline (not dumping hundreds of raw logs)
    all_events = timeline_ctx["events"]
    # Filter key events: anomalies, critical/high severity, or distinct actions
    milestones = [e for e in all_events if e.get("is_anomaly") or e.get("severity") in ("critical", "high")]
    if len(milestones) < 12:
        # fill remaining with regular events spread across time
        step = max(1, len(all_events) // (12 - len(milestones))) if len(all_events) > (12 - len(milestones)) else 1
        seen_ids = {m.get("id") or str(m.get("_id")) for m in milestones}
        for e in all_events[::step]:
            eid = e.get("id") or str(e.get("_id"))
            if eid not in seen_ids:
                milestones.append(e)
                if len(milestones) >= 12:
                    break

    milestones.sort(key=lambda x: str(x.get("timestamp", "")))
    key_timeline = milestones[:12]

    for ev in key_timeline:
        ev["description"] = _get_plain_description(ev)
        ts = ev.get("timestamp")
        if isinstance(ts, datetime):
            ev["timestamp_str"] = ts.strftime("%Y-%m-%d %H:%M:%S")

    # Collect MITRE techniques from anomalies + correlations
    all_technique_ids: set = set()
    for a in anomalies_top:
        for t in a.get("mitre_techniques", []):
            all_technique_ids.add(t)
    for c in correlations:
        if c.get("mitre"):
            all_technique_ids.add(c["mitre"])
    enriched_techniques = MitreMapper.enrich_techniques(list(all_technique_ids))

    # Limit graph edges for clean presentation
    if graph and "edges" in graph:
        graph["edges"] = graph["edges"][:10]

    return {
        "case": case,
        "case_id": case_id,
        "total_events": total_events,
        "anomalies_count": anomalies_count,
        "critical_high_count": critical_high_count,
        "anomalies": anomalies_top,
        "graph": graph,
        "correlations": correlations[:8],
        "enriched_techniques": enriched_techniques[:8],
        "timeline": key_timeline,
        "sessions": timeline_ctx["sessions"][:5],
        "span_hours": timeline_ctx["span_hours"],
        "evidence_list": evidence_list,
        "date_generated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
