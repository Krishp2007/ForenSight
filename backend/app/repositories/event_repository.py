from typing import Optional, Dict, Any, List
from bson import ObjectId
from backend.app.db.mongodb import db_client

class EventRepository:
    @staticmethod
    async def bulk_create(events: List[Dict[str, Any]]) -> int:
        """Insert a batch of event documents into MongoDB. Returns number of inserted records."""
        if not events:
            return 0
        try:
            result = await db_client.db["events"].insert_many(events, ordered=False)
            return len(result.inserted_ids)
        except Exception as e:
            # If some insert fails, insert what we can
            return 0

    @staticmethod
    async def list_by_case(
        case_id: str,
        org_id: str,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
        is_anomaly: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve events in a case matching criteria with skip/limit pagination, scoped by organization ID."""
        try:
            if not ObjectId.is_valid(case_id) or not ObjectId.is_valid(org_id):
                return []
                
            query = {
                "case_id": ObjectId(case_id),
                "organization_id": ObjectId(org_id)
            }
            
            if severity:
                query["severity"] = severity
            if event_type:
                query["event_type"] = event_type
            if is_anomaly is not None:
                query["is_anomaly"] = is_anomaly
                
            cursor = db_client.db["events"].find(query).sort("timestamp", 1).skip(skip).limit(limit)
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

    @staticmethod
    async def delete_by_evidence(evidence_id: str, org_id: str) -> int:
        """Delete all events associated with a specific evidence ID in MongoDB."""
        try:
            if not ObjectId.is_valid(evidence_id) or not ObjectId.is_valid(org_id):
                return 0
            result = await db_client.db["events"].delete_many({
                "evidence_id": ObjectId(evidence_id),
                "organization_id": ObjectId(org_id)
            })
            return result.deleted_count
        except Exception:
            return 0
