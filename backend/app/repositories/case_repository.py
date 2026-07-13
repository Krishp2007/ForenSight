from typing import Optional, Dict, Any, List
from bson import ObjectId
from backend.app.db.mongodb import db_client

class CaseRepository:
    @staticmethod
    async def get_by_id(case_id: str, org_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve case document scoped by organization ID."""
        try:
            if not ObjectId.is_valid(case_id) or not ObjectId.is_valid(org_id):
                return None
            return await db_client.db["cases"].find_one({
                "_id": ObjectId(case_id),
                "organization_id": ObjectId(org_id)
            })
        except Exception:
            return None

    @staticmethod
    async def create(case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new case document into MongoDB."""
        result = await db_client.db["cases"].insert_one(case_data)
        case_data["_id"] = result.inserted_id
        return case_data

    @staticmethod
    async def list_by_org(org_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List cases belonging to a specific organization, optionally filtered by status."""
        try:
            if not ObjectId.is_valid(org_id):
                return []
            
            query = {"organization_id": ObjectId(org_id)}
            if status:
                query["status"] = status
                
            cursor = db_client.db["cases"].find(query)
            return await cursor.to_list(length=100)
        except Exception:
            return []

    @staticmethod
    async def update(case_id: str, org_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update case document scoped by organization ID."""
        try:
            if not ObjectId.is_valid(case_id) or not ObjectId.is_valid(org_id):
                return None
            
            result = await db_client.db["cases"].find_one_and_update(
                {"_id": ObjectId(case_id), "organization_id": ObjectId(org_id)},
                {"$set": update_data},
                return_document=True
            )
            return result
        except Exception:
            return None
