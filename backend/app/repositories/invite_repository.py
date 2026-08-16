import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from bson import ObjectId
from backend.app.db.mongodb import db_client

class InviteRepository:
    @staticmethod
    async def create_invite(
        organization_id: str,
        role: str,
        created_by: Optional[str] = None,
        target_email: Optional[str] = None,
        expires_in_days: int = 7
    ) -> Dict[str, Any]:
        """Generate and save a new organization invite token in MongoDB."""
        now = datetime.utcnow()
        expires_at = now + timedelta(days=expires_in_days)
        token = secrets.token_urlsafe(32)

        record = {
            "token": token,
            "organization_id": ObjectId(organization_id),
            "role": role,
            "created_by": ObjectId(created_by) if created_by and ObjectId.is_valid(created_by) else None,
            "target_email": target_email.lower().strip() if target_email else None,
            "created_at": now,
            "expires_at": expires_at,
            "is_used": False,
            "used_by": None,
            "used_at": None,
        }

        result = await db_client.db["invites"].insert_one(record)
        record["_id"] = result.inserted_id
        return record

    @staticmethod
    async def get_by_token(token: str) -> Optional[Dict[str, Any]]:
        """Retrieve an invite record by its raw token string."""
        try:
            return await db_client.db["invites"].find_one({"token": token})
        except Exception:
            return None

    @classmethod
    async def get_valid_invite(cls, token: str) -> Optional[Dict[str, Any]]:
        """Retrieve an active, unused, and unexpired invite token."""
        invite = await cls.get_by_token(token)
        if not invite:
            return None

        if invite.get("is_used", False):
            return None

        expires_at = invite.get("expires_at")
        if expires_at and datetime.utcnow() > expires_at:
            return None

        return invite

    @staticmethod
    async def mark_used(token: str, user_id: str) -> bool:
        """Mark an invite token as consumed by a registered user."""
        now = datetime.utcnow()
        result = await db_client.db["invites"].update_one(
            {"token": token, "is_used": False},
            {
                "$set": {
                    "is_used": True,
                    "used_by": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id,
                    "used_at": now
                }
            }
        )
        return result.modified_count > 0

    @staticmethod
    async def list_by_org(organization_id: str) -> List[Dict[str, Any]]:
        """List all invite records for a specific organization."""
        try:
            if not ObjectId.is_valid(organization_id):
                return []
            cursor = db_client.db["invites"].find(
                {"organization_id": ObjectId(organization_id)}
            ).sort("created_at", -1)
            return await cursor.to_list(length=100)
        except Exception:
            return []

    @staticmethod
    async def revoke_invite(invite_id: str, organization_id: str) -> bool:
        """Revoke an active invite token by setting is_used=True."""
        try:
            if not ObjectId.is_valid(invite_id) or not ObjectId.is_valid(organization_id):
                return False
            result = await db_client.db["invites"].update_one(
                {
                    "_id": ObjectId(invite_id),
                    "organization_id": ObjectId(organization_id),
                    "is_used": False
                },
                {"$set": {"is_used": True, "revoked_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception:
            return False
