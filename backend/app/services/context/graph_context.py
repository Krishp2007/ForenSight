"""
Graph Context Builder — ForenSight AI
=========================================
Fetches derived DERIVED_CORRELATION relationships from Neo4j and
formats them for the copilot prompt and report generator.
"""

import logging
from typing import Any, Dict, List
from backend.app.services.graph.graph_queries import GraphCorrelationRules

logger = logging.getLogger(__name__)


async def build_graph_context(
    case_id: str, org_id: str
) -> List[Dict[str, Any]]:
    """
    Return all DERIVED_CORRELATION relationships for a case.
    Each item contains: rule, source, target, mitre, technique, derived_at.
    """
    summary = await GraphCorrelationRules.get_correlation_summary(case_id, org_id)
    correlations = summary.get("correlations", [])
    logger.debug(f"Fetched {len(correlations)} correlations for case {case_id}")
    return correlations
