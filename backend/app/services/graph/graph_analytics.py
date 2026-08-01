"""
Graph Analytics — ForenSight AI
==================================
Computes structural metrics over the case knowledge graph stored in Neo4j.

Provides:
  - Degree centrality  — which entities appear most often as source or target
  - Top attack paths   — longest FORENSIC_ACTION chains (depth-first traversal)
  - Anomaly hotspots   — nodes connected to the most anomalous edges
  - Entity type summary— count of each node type (Process, File, NetworkAddress…)

All queries are scoped by case_id + organization_id for tenant isolation.
"""

import logging
from typing import Any, Dict, List

from backend.app.db.neo4j import neo4j_client

logger = logging.getLogger(__name__)


class GraphAnalytics:

    @staticmethod
    async def degree_centrality(
        case_id: str, org_id: str, top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Return the top-N most connected entity nodes by total degree
        (in-degree + out-degree on FORENSIC_ACTION edges).

        Each result: { name, type, in_degree, out_degree, total_degree }
        """
        driver = neo4j_client.driver
        if not driver:
            return []

        cypher = """
        MATCH (n:Entity {case_id: $case_id, organization_id: $org_id})
        OPTIONAL MATCH (n)-[out:FORENSIC_ACTION {case_id: $case_id, organization_id: $org_id}]->()
        OPTIONAL MATCH ()-[in:FORENSIC_ACTION  {case_id: $case_id, organization_id: $org_id}]->(n)
        RETURN
            n.name  AS name,
            n.type  AS type,
            count(DISTINCT out) AS out_degree,
            count(DISTINCT in)  AS in_degree,
            count(DISTINCT out) + count(DISTINCT in) AS total_degree
        ORDER BY total_degree DESC
        LIMIT $top_n
        """
        try:
            async with driver.session() as session:
                result = await session.run(
                    cypher, case_id=case_id, org_id=org_id, top_n=top_n
                )
                return await result.data()
        except Exception as e:
            logger.error(f"[GraphAnalytics] degree_centrality failed: {e}")
            return []

    @staticmethod
    async def anomaly_hotspots(
        case_id: str, org_id: str, top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Return the top-N entity nodes that appear most often in anomalous
        FORENSIC_ACTION edges (is_anomaly = true).

        Each result: { name, type, anomaly_edge_count }
        """
        driver = neo4j_client.driver
        if not driver:
            return []

        cypher = """
        MATCH (n:Entity {case_id: $case_id, organization_id: $org_id})
              -[r:FORENSIC_ACTION {case_id: $case_id, organization_id: $org_id, is_anomaly: true}]->()
        RETURN n.name AS name, n.type AS type, count(r) AS anomaly_edge_count
        ORDER BY anomaly_edge_count DESC
        LIMIT $top_n
        """
        try:
            async with driver.session() as session:
                result = await session.run(
                    cypher, case_id=case_id, org_id=org_id, top_n=top_n
                )
                return await result.data()
        except Exception as e:
            logger.error(f"[GraphAnalytics] anomaly_hotspots failed: {e}")
            return []

    @staticmethod
    async def entity_type_summary(
        case_id: str, org_id: str
    ) -> List[Dict[str, Any]]:
        """
        Return a breakdown of entity node counts by type.
        e.g. [{ type: "Process", count: 42 }, { type: "File", count: 18 }, ...]
        """
        driver = neo4j_client.driver
        if not driver:
            return []

        cypher = """
        MATCH (n:Entity {case_id: $case_id, organization_id: $org_id})
        RETURN n.type AS type, count(n) AS count
        ORDER BY count DESC
        """
        try:
            async with driver.session() as session:
                result = await session.run(cypher, case_id=case_id, org_id=org_id)
                return await result.data()
        except Exception as e:
            logger.error(f"[GraphAnalytics] entity_type_summary failed: {e}")
            return []

    @staticmethod
    async def action_frequency(
        case_id: str, org_id: str, top_n: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Return the most frequent action types (relationship labels) in the graph.
        e.g. [{ action: "spawned", count: 120 }, ...]
        """
        driver = neo4j_client.driver
        if not driver:
            return []

        cypher = """
        MATCH ()-[r:FORENSIC_ACTION {case_id: $case_id, organization_id: $org_id}]->()
        RETURN r.action AS action, count(r) AS count
        ORDER BY count DESC
        LIMIT $top_n
        """
        try:
            async with driver.session() as session:
                result = await session.run(
                    cypher, case_id=case_id, org_id=org_id, top_n=top_n
                )
                return await result.data()
        except Exception as e:
            logger.error(f"[GraphAnalytics] action_frequency failed: {e}")
            return []

    @classmethod
    async def full_summary(cls, case_id: str, org_id: str) -> Dict[str, Any]:
        """
        Run all analytics in parallel and return a combined summary dict.
        Used by the graph API and report context builder.
        """
        import asyncio
        centrality, hotspots, types, actions = await asyncio.gather(
            cls.degree_centrality(case_id, org_id),
            cls.anomaly_hotspots(case_id, org_id),
            cls.entity_type_summary(case_id, org_id),
            cls.action_frequency(case_id, org_id),
        )
        return {
            "top_entities_by_degree": centrality,
            "anomaly_hotspots": hotspots,
            "entity_type_breakdown": types,
            "top_actions": actions,
        }
