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


async def build_report_context(case_id: str, org_id: str) -> Dict[str, Any]:
    """
    Gather all structured data required by the report Jinja2 template.

    Returns
    -------
    {
      case, case_id, total_events, anomalies_count, critical_high_count,
      anomalies, graph, correlations, enriched_techniques,
      timeline, sessions, date_generated
    }
    """
    case = await CaseRepository.get_by_id(case_id, org_id)
    if not case:
        raise ValueError(f"Case {case_id} not found for org {org_id}")

    # Parallel fetch where possible with exception safety
    import asyncio
    results = await asyncio.gather(
        build_anomaly_context(case, limit=100),
        build_graph_context(case_id, org_id),
        GraphRepository.get_case_graph(case_id, org_id),
        build_timeline_context(case, limit=500),
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

    # Aggregate counts via EventRepository to match Dashboard stats exactly
    from backend.app.repositories.event_repository import EventRepository
    stats_data = await EventRepository.count_case_stats(case_id, org_id)
    total_events = stats_data["total"]
    anomalies_count = stats_data["anomalies"]
    critical_high_count = stats_data["critical"]

    # Collect MITRE techniques from anomalies + correlations
    all_technique_ids: set = set()
    for a in anomalies:
        for t in a.get("mitre_techniques", []):
            all_technique_ids.add(t)
    for c in correlations:
        if c.get("mitre"):
            all_technique_ids.add(c["mitre"])
    enriched_techniques = MitreMapper.enrich_techniques(list(all_technique_ids))

    # Format anomaly timestamps for display
    for a in anomalies:
        ts = a.get("timestamp")
        if isinstance(ts, datetime):
            a["timestamp"] = ts.strftime("%Y-%m-%d %H:%M:%S")

    return {
        "case": case,
        "case_id": case_id,
        "total_events": total_events,
        "anomalies_count": anomalies_count,
        "critical_high_count": critical_high_count,
        "anomalies": anomalies,
        "graph": graph,
        "correlations": correlations,
        "enriched_techniques": enriched_techniques,
        "timeline": timeline_ctx["events"][:50],  # top 50 for report
        "sessions": timeline_ctx["sessions"],
        "span_hours": timeline_ctx["span_hours"],
        "date_generated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
