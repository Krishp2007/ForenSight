"""
Graph Correlation Rules — ForenSight AI
========================================
Architecture Section 5.5.1: Rule-based correlation.

Three hand-written Cypher rules that derive higher-order forensic facts
from the raw FORENSIC_ACTION edges already in Neo4j:

  Rule 1 — PROCESS_INITIATED_CONNECTION
    Binds a process execution event to a network connection event that
    happened within a short time window (temporal-proximity binding).

  Rule 2 — REGISTRY_RUN_KEY_PERSISTENCE
    Detects registry Run/RunOnce key writes — the classic Windows
    autostart persistence technique (MITRE T1547.001).

  Rule 3 — PARENT_CHILD_PROCESS_CHAIN
    Matches process-spawn edges to build an explicit PARENT_OF chain
    between process entities, enabling "who spawned whom" traversals.

Each rule:
  - Reads a pattern from the graph
  - Asserts a new derived DERIVED_CORRELATION relationship
  - Stores provenance: which rule triggered it, at what timestamp,
    and which source event_ids were used
"""

import logging
from datetime import datetime
from typing import Dict, Any

from backend.app.db.neo4j import neo4j_client

logger = logging.getLogger(__name__)


class GraphCorrelationRules:

    # ── Rule 1 — Process-to-Network temporal binding ─────────────────────────

    RULE_PROCESS_TO_NETWORK = """
    // Rule 1: Process-to-Network Connection Binding
    // Find a process execution event followed by a network connection from the
    // same subject within a 5-minute window. Assert PROCESS_INITIATED_CONNECTION.
    MATCH (proc:Entity {case_id: $case_id, organization_id: $org_id})
          -[exec:FORENSIC_ACTION {case_id: $case_id, organization_id: $org_id}]->
          (target:Entity)
    WHERE exec.action IN ['spawned', 'executed', 'process_creation', 'exec']

    MATCH (proc)-[conn:FORENSIC_ACTION {case_id: $case_id, organization_id: $org_id}]->
          (net:Entity)
    WHERE conn.action IN ['connected_to', 'network_connection', 'connect', 'send']
      AND net.type IN ['NetworkAddress', 'GenericEntity']
      AND duration.between(
            datetime(exec.timestamp),
            datetime(conn.timestamp)
          ).minutes <= 5
      AND duration.between(
            datetime(exec.timestamp),
            datetime(conn.timestamp)
          ).minutes >= 0

    MERGE (proc)-[derived:DERIVED_CORRELATION {
        rule: 'PROCESS_INITIATED_CONNECTION',
        case_id: $case_id,
        organization_id: $org_id
    }]->(net)
    ON CREATE SET
        derived.derived_at      = $now,
        derived.exec_event_id   = exec.event_id,
        derived.conn_event_id   = conn.event_id,
        derived.process_name    = proc.name,
        derived.network_target  = net.name,
        derived.time_delta_mins = duration.between(
                                      datetime(exec.timestamp),
                                      datetime(conn.timestamp)
                                  ).minutes

    RETURN count(derived) AS created
    """

    # ── Rule 2 — Registry Run-Key Persistence ────────────────────────────────

    RULE_RUN_KEY_PERSISTENCE = """
    // Rule 2: Registry Run/RunOnce Key Persistence (MITRE T1547.001)
    // Any FORENSIC_ACTION whose object contains a Run or RunOnce registry path
    // is flagged as a PERSISTENCE_TECHNIQUE derived relation.
    MATCH (actor:Entity {case_id: $case_id, organization_id: $org_id})
          -[reg:FORENSIC_ACTION {case_id: $case_id, organization_id: $org_id}]->
          (key:Entity {case_id: $case_id, organization_id: $org_id})
    WHERE (
        toLower(key.name) CONTAINS 'currentversion\\\\run'
        OR toLower(key.name) CONTAINS 'currentversion\\\\runonce'
        OR toLower(key.name) CONTAINS 'software\\\\microsoft\\\\windows'
    )
    AND reg.action IN [
        'registry_change', 'modified', 'created', 'set_value', 'write'
    ]

    MERGE (actor)-[derived:DERIVED_CORRELATION {
        rule: 'REGISTRY_RUN_KEY_PERSISTENCE',
        case_id: $case_id,
        organization_id: $org_id
    }]->(key)
    ON CREATE SET
        derived.derived_at    = $now,
        derived.source_event  = reg.event_id,
        derived.mitre         = 'T1547.001',
        derived.technique     = 'Boot or Logon Autostart Execution: Registry Run Keys',
        derived.actor_name    = actor.name,
        derived.registry_key  = key.name

    RETURN count(derived) AS created
    """

    # ── Rule 3 — Parent-Child Process Chain ──────────────────────────────────

    RULE_PARENT_CHILD_CHAIN = """
    // Rule 3: Parent-Child Process Chain
    // Where one process entity 'spawned' or 'executed' another process entity,
    // assert an explicit PARENT_OF derived relationship for clean traversal.
    MATCH (parent:Entity {case_id: $case_id, organization_id: $org_id})
          -[spawn:FORENSIC_ACTION {case_id: $case_id, organization_id: $org_id}]->
          (child:Entity {case_id: $case_id, organization_id: $org_id})
    WHERE spawn.action IN ['spawned', 'executed', 'process_creation', 'exec', 'created_process']
      AND (
          parent.type IN ['Process', 'GenericEntity']
          OR toLower(parent.name) ENDS WITH '.exe'
      )
      AND (
          child.type IN ['Process', 'GenericEntity']
          OR toLower(child.name) ENDS WITH '.exe'
          OR toLower(child.name) CONTAINS 'powershell'
          OR toLower(child.name) CONTAINS 'cmd'
          OR toLower(child.name) CONTAINS 'wscript'
          OR toLower(child.name) CONTAINS 'cscript'
      )

    MERGE (parent)-[derived:DERIVED_CORRELATION {
        rule: 'PARENT_OF',
        case_id: $case_id,
        organization_id: $org_id
    }]->(child)
    ON CREATE SET
        derived.derived_at   = $now,
        derived.source_event = spawn.event_id,
        derived.parent_name  = parent.name,
        derived.child_name   = child.name,
        derived.timestamp    = spawn.timestamp

    RETURN count(derived) AS created
    """

    @classmethod
    async def run_all_rules(cls, case_id: str, org_id: str) -> Dict[str, Any]:
        """
        Execute all three correlation rules against a case's graph.
        Returns a summary of how many derived relationships were created by each rule.
        """
        driver = neo4j_client.driver
        if not driver:
            logger.warning("Neo4j not available — skipping correlation rules.")
            return {"skipped": True}

        now = datetime.utcnow().isoformat()
        params = {"case_id": case_id, "org_id": org_id, "now": now}
        results = {}

        rules = [
            ("process_to_network", cls.RULE_PROCESS_TO_NETWORK),
            ("run_key_persistence", cls.RULE_RUN_KEY_PERSISTENCE),
            ("parent_child_chain", cls.RULE_PARENT_CHILD_CHAIN),
        ]

        for rule_name, cypher in rules:
            try:
                async with driver.session() as session:
                    result = await session.run(cypher, **params)
                    record = await result.single()
                    count = record["created"] if record else 0
                    results[rule_name] = count
                    logger.info(
                        f"[CORRELATION] Rule '{rule_name}' derived {count} "
                        f"relationships for case {case_id}"
                    )
            except Exception as e:
                logger.error(f"[CORRELATION] Rule '{rule_name}' failed: {e}")
                results[rule_name] = f"error: {e}"

        return results

    @classmethod
    async def get_correlation_summary(cls, case_id: str, org_id: str) -> Dict[str, Any]:
        """
        Query and return all derived correlations for a case.
        Useful for the copilot context and the report generator.
        """
        driver = neo4j_client.driver
        if not driver:
            return {"correlations": []}

        cypher = """
        MATCH (s:Entity {case_id: $case_id, organization_id: $org_id})
              -[r:DERIVED_CORRELATION {case_id: $case_id, organization_id: $org_id}]->
              (t:Entity)
        RETURN
            r.rule         AS rule,
            s.name         AS source,
            t.name         AS target,
            r.mitre        AS mitre,
            r.technique    AS technique,
            r.derived_at   AS derived_at,
            r.source_event AS source_event
        ORDER BY r.derived_at DESC
        LIMIT 500
        """
        try:
            async with driver.session() as session:
                result = await session.run(cypher, case_id=case_id, org_id=org_id)
                rows = await result.data()
            return {"correlations": rows, "total": len(rows)}
        except Exception as e:
            logger.error(f"Failed fetching correlation summary: {e}")
            return {"correlations": [], "total": 0}
