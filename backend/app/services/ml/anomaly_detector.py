import logging
import numpy as np
import asyncio
from typing import List, Dict, Any
from sklearn.ensemble import IsolationForest
from bson import ObjectId

from backend.app.db.mongodb import db_client
from backend.app.repositories.event_repository import EventRepository
from backend.app.db.neo4j import neo4j_client

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {
    "info": 0.0,
    "low": 0.25,
    "medium": 0.5,
    "high": 0.75,
    "critical": 1.0
}

class AnomalyDetector:
    @staticmethod
    async def detect_and_update_anomalies(case_id: str, org_id: str) -> Dict[str, Any]:
        """Fetch all case events, train an Isolation Forest model, and write anomaly scores back to Mongo/Neo4j."""
        logger.info(f"Starting anomaly detection for case_id={case_id} org_id={org_id}")
        
        # 1. Fetch events from MongoDB
        events = await EventRepository.list_by_case(case_id, org_id, limit=5000)
        total_events = len(events)
        
        if total_events < 5:
            logger.info(f"Insufficient events ({total_events}) for anomaly detection. Minimum is 5. Aborting.")
            return {
                "status": "skipped",
                "reason": f"Insufficient events ({total_events}). Minimum required is 5.",
                "anomalies_detected": 0
            }
            
        # 2. Extract features for vectorization
        # Compute frequency maps for subjects, actions, and objects within this case context
        subjects = [e.get("subject", "") for e in events]
        objects = [e.get("object", "") for e in events]
        actions = [e.get("action", "") for e in events]
        
        from collections import Counter
        subj_counts = Counter(subjects)
        obj_counts = Counter(objects)
        act_counts = Counter(actions)
        
        features_list = []
        for e in events:
            # Timestamp components
            ts = e.get("timestamp")
            if ts and hasattr(ts, "hour"):
                hour = ts.hour
                weekday = ts.weekday()
                is_weekend = 1.0 if weekday >= 5 else 0.0
            else:
                hour = 12.0
                is_weekend = 0.0
                
            # Category frequency scores (normalized by total events)
            subj_freq = subj_counts[e.get("subject", "")] / total_events
            obj_freq = obj_counts[e.get("object", "")] / total_events
            act_freq = act_counts[e.get("action", "")] / total_events
            
            # Severity values
            sev = e.get("severity", "info").lower()
            sev_val = SEVERITY_WEIGHTS.get(sev, 0.0)
            
            features_list.append([
                hour,
                is_weekend,
                subj_freq,
                obj_freq,
                act_freq,
                sev_val
            ])
            
        # 3. Train Isolation Forest model
        X = np.array(features_list)
        
        # We flag roughly the top 5% most anomalous entries as outliers
        # If the number of events is very low, we set contamination to auto
        contamination = 0.05 if total_events >= 20 else "auto"
        
        model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        
        # Fit model and predict
        # predictions are 1 for inliers, -1 for outliers
        preds = model.fit_predict(X)
        
        # Decision function returns raw anomaly score (lower is more anomalous)
        # We normalize this to a [0.0, 1.0] range where values closer to 1.0 are outliers
        raw_scores = model.decision_function(X)
        min_score = np.min(raw_scores)
        max_score = np.max(raw_scores)
        
        # Safeguard division by zero if all scores are identical
        if max_score - min_score > 0:
            norm_scores = 1.0 - ((raw_scores - min_score) / (max_score - min_score))
        else:
            norm_scores = np.zeros(len(raw_scores))
            
        # 4. Bulk update MongoDB events
        anomalies_count = 0
        mongo_bulk_ops = []
        
        for idx, event in enumerate(events):
            event_id = event["_id"]
            is_anomaly = bool(preds[idx] == -1)
            anomaly_score = float(norm_scores[idx])
            
            if is_anomaly:
                anomalies_count += 1
                
            # Prepare update operation
            mongo_bulk_ops.append(
                db_client.db["events"].update_one(
                    {"_id": event_id},
                    {"$set": {
                        "is_anomaly": is_anomaly,
                        "anomaly_score": anomaly_score
                    }}
                )
            )
            
        if mongo_bulk_ops:
            await asyncio.gather(*mongo_bulk_ops)
            
        logger.info(f"MongoDB events updated. Flagged {anomalies_count} anomalies out of {total_events} events.")
        
        # 5. Sync anomaly status to Neo4j
        # We update relationship attributes inside the case graph so threat visualizers can highlight edges
        driver = neo4j_client.driver
        if driver:
            cypher_query = """
            UNWIND $batch AS item
            MATCH (s:Entity {case_id: $case_id, organization_id: $org_id})-[r:FORENSIC_ACTION {event_id: item.event_id}]->(o:Entity {case_id: $case_id, organization_id: $org_id})
            SET r.is_anomaly = item.is_anomaly, r.anomaly_score = item.anomaly_score
            """
            
            neo4j_batch = []
            for idx, event in enumerate(events):
                neo4j_batch.append({
                    "event_id": str(event["_id"]),
                    "is_anomaly": bool(preds[idx] == -1),
                    "anomaly_score": float(norm_scores[idx])
                })
                
            try:
                async with driver.session() as session:
                    await session.run(cypher_query, batch=neo4j_batch, case_id=case_id, org_id=org_id)
                logger.info("Successfully updated anomaly labels in Neo4j case graph.")
            except Exception as ne:
                logger.error(f"Failed to update anomaly labels in Neo4j: {ne}")
                
        return {
            "status": "completed",
            "total_processed": total_events,
            "anomalies_detected": anomalies_count
        }
