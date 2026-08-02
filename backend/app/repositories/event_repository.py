from typing import Optional, Dict, Any, List
from bson import ObjectId
from backend.app.db.mongodb import db_client

class EventRepository:
    @staticmethod
    async def bulk_create(events: List[Dict[str, Any]]) -> int:
        """Insert events in chunks of 5000 to avoid MongoDB write timeout on large files."""
        if not events:
            return 0
        CHUNK = 5000
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
    async def list_by_case(
        case_id: str,
        org_id: str,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 2000
    ) -> List[Dict[str, Any]]:
        """Retrieve events in a case matching criteria, scoped by organization ID."""
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
