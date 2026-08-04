import logging
import re
from typing import List, Dict, Any
from backend.app.db.neo4j import neo4j_client

logger = logging.getLogger(__name__)

# Basic helpers to infer entity types from names
IP_PATTERN = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$")
FILE_EXT_PATTERN = re.compile(r"\.[a-zA-Z0-9]{2,4}$")

class GraphRepository:
    @staticmethod
    def infer_entity_type(name: str) -> str:
        """Categorize entity node based on name formatting cues."""
        name_clean = name.strip().lower()
        if IP_PATTERN.match(name_clean) or "dns:" in name_clean or "http:" in name_clean or "https:" in name_clean:
            return "NetworkAddress"
        elif any(ext in name_clean for ext in (".exe", ".dll", ".ps1", ".vbs", ".bat", ".cmd", ".sh")):
            return "Process"
        elif "\\" in name or "/" in name or FILE_EXT_PATTERN.search(name_clean):
            return "File"
        elif name_clean.startswith("hkey_") or "registry" in name_clean:
            return "RegistryKey"
        elif any(u in name_clean for u in ("user", "admin", "system", "authority")):
            return "User"
        return "GenericEntity"

    @classmethod
    async def bulk_import_events(cls, events: List[Dict[str, Any]]) -> int:
        """Translate CFM event list into Neo4j nodes and edges."""
        if not events:
            return 0
            
        driver = neo4j_client.driver
        if not driver:
            logger.warning("Neo4j driver not initialized. Skipping graph sync.")
            return 0
            
        cypher_query = """
        UNWIND $batch AS event
        MERGE (s:Entity {name: event.subject, case_id: event.case_id, organization_id: event.organization_id})
        ON CREATE SET s.type = event.subject_type
        
        MERGE (o:Entity {name: event.object, case_id: event.case_id, organization_id: event.organization_id})
        ON CREATE SET o.type = event.object_type
        
        CREATE (s)-[r:FORENSIC_ACTION {
            action: event.action,
            timestamp: event.timestamp,
            severity: event.severity,
            event_id: event.event_id,
            case_id: event.case_id,
            organization_id: event.organization_id
        }]->(o)
        """
        
        # Prepare parameters batch
        batch = []
        for e in events:
            # Skip incomplete events
            if not e.get("subject") or not e.get("object"):
                continue
                
            subj = str(e["subject"])
            obj = str(e["object"])
            
            batch.append({
                "subject": subj,
                "subject_type": cls.infer_entity_type(subj),
                "object": obj,
                "object_type": cls.infer_entity_type(obj),
                "action": str(e["action"]),
                "timestamp": e["timestamp"].isoformat() if hasattr(e["timestamp"], "isoformat") else str(e["timestamp"]),
                "severity": str(e["severity"]),
                "event_id": str(e["_id"]) if "_id" in e else str(e.get("id", "")),
                "case_id": str(e["case_id"]),
                "organization_id": str(e["organization_id"])
            })
            
        if not batch:
            return 0
            
        # Chunk batch to avoid Neo4j database lock timeouts and transaction memory issues
        BATCH_SIZE = 1000
        synced_count = 0
        try:
            async with driver.session() as session:
                for i in range(0, len(batch), BATCH_SIZE):
                    chunk = batch[i:i + BATCH_SIZE]
                    await session.run(cypher_query, batch=chunk)
                    synced_count += len(chunk)
            logger.info(f"Successfully synced {synced_count} event nodes/relationships to Neo4j.")
            return synced_count
        except Exception as ex:
            logger.error(f"Failed bulk importing events into Neo4j: {ex}")
            return synced_count

    @staticmethod
    async def get_case_graph(case_id: str, org_id: str) -> Dict[str, List[Any]]:
        """Retrieve all nodes and edges scoped by case and organization in D3-link format."""
        driver = neo4j_client.driver
        if not driver:
            return {"nodes": [], "edges": []}
            
        cypher_query = """
        MATCH (s:Entity {case_id: $case_id, organization_id: $org_id})-[r:FORENSIC_ACTION {case_id: $case_id, organization_id: $org_id}]->(o:Entity {case_id: $case_id, organization_id: $org_id})
        RETURN s.name AS source_name, s.type AS source_type,
               o.name AS target_name, o.type AS target_type,
               r.action AS action, r.severity AS severity, r.timestamp AS timestamp, r.event_id AS event_id,
               r.is_anomaly AS is_anomaly, r.anomaly_score AS anomaly_score
        LIMIT 1000
        """
        
        nodes_dict = {}
        edges = []
        
        try:
            async with driver.session() as session:
                result = await session.run(cypher_query, case_id=case_id, org_id=org_id)
                records = await result.data()
                
                for record in records:
                    s_name = record["source_name"]
                    s_type = record["source_type"]
                    t_name = record["target_name"]
                    t_type = record["target_type"]
                    
                    # Track unique nodes
                    if s_name not in nodes_dict:
                        nodes_dict[s_name] = {"id": s_name, "label": s_name, "type": s_type}
                    if t_name not in nodes_dict:
                        nodes_dict[t_name] = {"id": t_name, "label": t_name, "type": t_type}
                        
                    # Add edge
                    edges.append({
                        "source": s_name,
                        "target": t_name,
                        "action": record["action"],
                        "severity": record["severity"],
                        "timestamp": record["timestamp"],
                        "event_id": record["event_id"],
                        "is_anomaly": record.get("is_anomaly", False),
                        "anomaly_score": record.get("anomaly_score", 0.0)
                    })
                    
            return {
                "nodes": list(nodes_dict.values()),
                "edges": edges
            }
        except Exception as e:
            logger.error(f"Failed to fetch case graph from Neo4j: {e}")
            return {"nodes": [], "edges": []}

    @staticmethod
    async def clear_case_graph(case_id: str, org_id: str):
        """Delete case nodes and relationships from Neo4j."""
        driver = neo4j_client.driver
        if not driver:
            return
        cypher_query = """
        MATCH (n:Entity {case_id: $case_id, organization_id: $org_id})
        DETACH DELETE n
        """
        try:
            async with driver.session() as session:
                await session.run(cypher_query, case_id=case_id, org_id=org_id)
            logger.info(f"Cleared Neo4j graph nodes for case {case_id}")
        except Exception as e:
            logger.error(f"Failed to clear case graph from Neo4j: {e}")

    @staticmethod
    async def delete_events_by_id(event_ids: List[str], case_id: str, org_id: str) -> bool:
        """Delete forensic action relationships and orphan Entity nodes by event IDs."""
        driver = neo4j_client.driver
        if not driver or not event_ids:
            return False
            
        cypher_query_rels = """
        UNWIND $event_ids AS eid
        MATCH (s:Entity {case_id: $case_id, organization_id: $org_id})-[r:FORENSIC_ACTION {event_id: eid}]->(o:Entity {case_id: $case_id, organization_id: $org_id})
        DELETE r
        """
        
        cypher_query_orphans = """
        MATCH (e:Entity {case_id: $case_id, organization_id: $org_id})
        WHERE NOT (e)-[:FORENSIC_ACTION]-()
        DELETE e
        """
        
        try:
            async with driver.session() as session:
                await session.run(cypher_query_rels, event_ids=event_ids, case_id=case_id, org_id=org_id)
                await session.run(cypher_query_orphans, case_id=case_id, org_id=org_id)
            logger.info(f"Successfully deleted {len(event_ids)} events from Neo4j graph.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete events in Neo4j: {e}")
            return False
