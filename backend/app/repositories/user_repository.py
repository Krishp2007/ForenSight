from typing import Optional, Dict, Any
from bson import ObjectId
from backend.app.db.mongodb import db_client

class UserRepository:
    @staticmethod
    async def get_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user document by MongoDB ObjectId string."""
        try:
            if not ObjectId.is_valid(user_id):
                return None
            return await db_client.db["users"].find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None

    @staticmethod
    async def get_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user document by unique email address."""
        try:
            return await db_client.db["users"].find_one({"email": email})
        except Exception:
            return None

    @staticmethod
    async def create(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user document in MongoDB."""
        result = await db_client.db["users"].insert_one(user_data)
        user_data["_id"] = result.inserted_id
        return user_data

    @staticmethod
    async def update(user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user fields by ID, return updated document."""
        if not ObjectId.is_valid(user_id):
            return None
        try:
            from pymongo import ReturnDocument
            result = await db_client.db["users"].find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": update_data},
                return_document=ReturnDocument.AFTER,
            )
            return result
        except Exception:
            return None

    @staticmethod
    async def list_by_org(org_id: str) -> list:
        """List all users in an organization (admin use)."""
        try:
            if not ObjectId.is_valid(org_id):
                return []
            cursor = db_client.db["users"].find(
                {"organization_id": ObjectId(org_id)},
                {"hashed_password": 0},   # never return password hash
            ).sort("created_at", -1)
            return await cursor.to_list(length=500)
        except Exception:
            return []
