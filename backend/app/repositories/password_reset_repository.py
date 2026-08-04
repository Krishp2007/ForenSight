from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
from bson import ObjectId
from backend.app.db.mongodb import db_client

class PasswordResetRepository:
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash raw token string using SHA256 before storing or querying database."""
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    @classmethod
    async def create_reset_token(cls, user_id: str, token: str, expires_in_minutes: int = 15) -> Dict[str, Any]:
        """Store a new password reset token entry in MongoDB."""
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=expires_in_minutes)
        token_hash = cls.hash_token(token)

        # Invalidate any existing unused reset tokens for this user
        await db_client.db["password_resets"].delete_many({"user_id": user_id})

        record = {
            "user_id": user_id,
            "token_hash": token_hash,
            "created_at": now,
            "expires_at": expires_at
        }
        result = await db_client.db["password_resets"].insert_one(record)
        record["_id"] = result.inserted_id
        return record

    @classmethod
    async def get_valid_token_record(cls, token: str) -> Optional[Dict[str, Any]]:
        """Retrieve active, non-expired password reset token record."""
        try:
            token_hash = cls.hash_token(token)
            record = await db_client.db["password_resets"].find_one({"token_hash": token_hash})
            if not record:
                return None
            
            # Check expiration
            if datetime.utcnow() > record.get("expires_at", datetime.min):
                await db_client.db["password_resets"].delete_one({"_id": record["_id"]})
                return None

            return record
        except Exception:
            return None

    @classmethod
    async def delete_token_record(cls, token: str) -> bool:
        """Delete password reset token record after successful reset."""
        try:
            token_hash = cls.hash_token(token)
            result = await db_client.db["password_resets"].delete_many({"token_hash": token_hash})
            return result.deleted_count > 0
        except Exception:
            return False
