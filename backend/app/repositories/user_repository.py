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
