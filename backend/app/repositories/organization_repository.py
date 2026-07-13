from typing import Optional, Dict, Any, List
from bson import ObjectId
from backend.app.db.mongodb import db_client

class OrganizationRepository:
    @staticmethod
    async def get_by_id(org_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve organization by its MongoDB ObjectId string."""
        try:
            if not ObjectId.is_valid(org_id):
                return None
            return await db_client.db["organizations"].find_one({"_id": ObjectId(org_id)})
        except Exception:
            return None

    @staticmethod
    async def get_by_name(name: str) -> Optional[Dict[str, Any]]:
        """Retrieve organization by its unique name (case-insensitive)."""
        try:
            return await db_client.db["organizations"].find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
        except Exception:
            return None

    @staticmethod
    async def create(org_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert new organization document into MongoDB."""
        result = await db_client.db["organizations"].insert_one(org_data)
        org_data["_id"] = result.inserted_id
        return org_data

    @staticmethod
    async def list_all() -> List[Dict[str, Any]]:
        """List all organizations in the database."""
        try:
            cursor = db_client.db["organizations"].find()
            return await cursor.to_list(length=100)
        except Exception:
            return []
