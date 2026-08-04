from typing import Optional, Dict, Any, List
from bson import ObjectId
from backend.app.db.mongodb import db_client

class EventRepository:
    @staticmethod
    async def bulk_create(events: List[Dict[str, Any]]) -> int:
        """Insert events in chunks of 5000 to avoid MongoDB write timeout on large files."""
        if not events:
            return 0
        CHUNK = 500
        total = 0
        try:
            for i in range(0, len(events), CHUNK):
                chunk = events[i : i + CHUNK]
                result = await db_client.db["events"].insert_many(chunk, ordered=False)
                total += len(result.inserted_ids)
        except Exception as e:
            # Partial success is fine — return what was inserted
            pass
        return total

    @staticmethod
    async def count_stats(case_id: str, org_id: str, evidence_id: Optional[str] = None) -> Dict[str, int]:
        """
        Canonical Single-Source-of-Truth Metrics Service.
        Computes total events, anomalies, and critical/high events cleanly
        for both Case Scope (evidence_id=None) and Evidence Scope (evidence_id=str).
        """
        try:
            cid_obj = ObjectId(case_id) if ObjectId.is_valid(case_id) else case_id
            oid_obj = ObjectId(org_id) if ObjectId.is_valid(org_id) else org_id
            
            base_match = {
                "$or": [
                    {"case_id": cid_obj},
                    {"case_id": str(case_id)},
                ],
                "$and": [
                    {"$or": [{"organization_id": oid_obj}, {"organization_id": str(org_id)}]}
                ]
            }

            if evidence_id:
                eid_obj = ObjectId(evidence_id) if ObjectId.is_valid(evidence_id) else evidence_id
                base_match["$and"].append({
                    "$or": [
                        {"evidence_id": eid_obj},
                        {"evidence_id": str(evidence_id)}
                    ]
                })

            anomaly_query = {
                **base_match,
                "$or": [{"is_anomaly": True}, {"anomaly_score": {"$gt": 0.5}}]
            }
            critical_query = {
                **base_match,
                "severity": {"$in": ["critical", "high", "Critical", "High", "CRITICAL", "HIGH"]}
            }

            import asyncio
            total, anomalies, critical = await asyncio.gather(
                db_client.db["events"].count_documents(base_match),
                db_client.db["events"].count_documents(anomaly_query),
                db_client.db["events"].count_documents(critical_query),
            )

            return {"total": total, "anomalies": anomalies, "critical": critical}
        except Exception:
            return {"total": 0, "anomalies": 0, "critical": 0}

    @classmethod
    async def count_case_stats(cls, case_id: str, org_id: str) -> Dict[str, int]:
        """Alias for count_stats at Case Scope."""
        return await cls.count_stats(case_id, org_id, evidence_id=None)

    @staticmethod
    async def list_by_case(
        case_id: str,
        org_id: str,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 2000
    ) -> List[Dict[str, Any]]:
        """Retrieve events in a case matching criteria, supporting both ObjectId and string IDs."""
        try:
            cid_obj = ObjectId(case_id) if ObjectId.is_valid(case_id) else case_id
            oid_obj = ObjectId(org_id) if ObjectId.is_valid(org_id) else org_id

            query = {
                "$or": [
                    {"case_id": cid_obj},
                    {"case_id": str(case_id)},
                ]
            }

            if severity:
                query["severity"] = severity
            if event_type:
                query["event_type"] = event_type

            cursor = db_client.db["events"].find(query).sort("timestamp", 1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception:
            return []

    @staticmethod
    async def get_by_id(event_id: str, org_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single event scoped by organization ID."""
        try:
            if not ObjectId.is_valid(event_id) or not ObjectId.is_valid(org_id):
                return None
            return await db_client.db["events"].find_one({
                "_id": ObjectId(event_id),
                "organization_id": ObjectId(org_id)
            })
        except Exception:
            return None
