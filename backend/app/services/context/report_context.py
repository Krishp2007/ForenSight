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

    # Parallel fetch where possible
    import asyncio
    (
        anomalies,
        correlations,
        graph,
        timeline_ctx,
    ) = await asyncio.gather(
        build_anomaly_context(case, limit=100),
        build_graph_context(case_id, org_id),
        GraphRepository.get_case_graph(case_id, org_id),
        build_timeline_context(case, limit=500),
    )

    # Aggregate counts
    total_events = await db_client.db["events"].count_documents(
        {"case_id": case["_id"], "organization_id": case["organization_id"]}
    )
    anomalies_count = await db_client.db["events"].count_documents(
        {"case_id": case["_id"], "organization_id": case["organization_id"], "is_anomaly": True}
    )
    critical_high_count = await db_client.db["events"].count_documents(
        {
            "case_id": case["_id"],
            "organization_id": case["organization_id"],
            "severity": {"$in": ["critical", "high"]},
        }
    )

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
        if ts and hasattr(ts, "strftime"):
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
