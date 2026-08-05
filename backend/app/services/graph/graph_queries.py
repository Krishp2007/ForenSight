"""
Graph Correlation Rules & Queries — ForenSight
================================================
Wrapper module connecting domain Cypher queries to GraphCorrelationEngine.
"""

import logging
from typing import Dict, Any
from backend.app.services.graph.graph_correlation import GraphCorrelationEngine

logger = logging.getLogger(__name__)


class GraphCorrelationRules:

    @classmethod
    async def run_all_rules(cls, case_id: str, org_id: str = "") -> Dict[str, Any]:
        """Execute correlation pipeline and return summary of findings."""
        res = await GraphCorrelationEngine.get_all_case_correlations(case_id)
        return {
            "total": res["total_correlations"],
            "findings": res["findings"],
            "process_chains": len([f for f in res["findings"] if f["type"] == "process_chain"]),
            "attack_paths": len([f for f in res["findings"] if f["type"] == "attack_path"]),
            "cross_evidence": len([f for f in res["findings"] if f["type"] == "cross_evidence"]),
        }

    @classmethod
    async def get_correlation_summary(cls, case_id: str, org_id: str = "") -> Dict[str, Any]:
        """Retrieve correlation summary dict."""
        res = await GraphCorrelationEngine.get_all_case_correlations(case_id)
        return {
            "case_id": case_id,
            "total": res["total_correlations"],
            "correlations": res["findings"],
        }
