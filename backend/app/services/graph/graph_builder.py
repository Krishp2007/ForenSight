"""
Graph Builder — ForenSight AI
================================
High-level helper that sits above GraphRepository and provides a clean
API for building and querying the case knowledge graph.

Used by the processing pipeline and copilot context builder to interact
with Neo4j without leaking Cypher details into application logic.
"""

import logging
from typing import Any, Dict, List

from backend.app.repositories.graph_repository import GraphRepository

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Orchestrates Neo4j graph construction from parsed forensic events.
    Wraps GraphRepository with higher-level semantics.
    """

    @staticmethod
    async def build_from_events(events: List[Dict[str, Any]]) -> int:
        """
        Import a list of enriched CFM events into Neo4j.
        Filters out any events missing subject or object before passing to the repository.

        Returns the number of events successfully synced.
        """
        valid = [e for e in events if e.get("subject") and e.get("object")]
        skipped = len(events) - len(valid)
        if skipped:
            logger.debug(f"[GraphBuilder] Skipped {skipped} events missing subject/object")
        if not valid:
            return 0
        return await GraphRepository.bulk_import_events(valid)

    @staticmethod
    async def get_graph(case_id: str, org_id: str) -> Dict[str, List[Any]]:
        """
        Return the full node-link graph for a case in D3-compatible format:
        { nodes: [{id, label, type}], edges: [{source, target, action, severity, ...}] }
        """
        return await GraphRepository.get_case_graph(case_id, org_id)

    @staticmethod
    async def clear(case_id: str, org_id: str) -> None:
        """Delete all nodes and edges for a case from Neo4j."""
        await GraphRepository.clear_case_graph(case_id, org_id)

    @staticmethod
    async def node_count(case_id: str, org_id: str) -> int:
        """Return the total number of Entity nodes for a case."""
        graph = await GraphRepository.get_case_graph(case_id, org_id)
        return len(graph.get("nodes", []))

    @staticmethod
    async def edge_count(case_id: str, org_id: str) -> int:
        """Return the total number of FORENSIC_ACTION edges for a case."""
        graph = await GraphRepository.get_case_graph(case_id, org_id)
        return len(graph.get("edges", []))
