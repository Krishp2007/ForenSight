import logging
from typing import Optional, Dict, Any, List
from bson import ObjectId
from backend.app.db.mongodb import db_client

logger = logging.getLogger(__name__)


class EvidenceRepository:

    @staticmethod
    async def get_by_id(evidence_id: str, org_id: str) -> Optional[Dict[str, Any]]:
        try:
            if not ObjectId.is_valid(evidence_id) or not ObjectId.is_valid(org_id):
                return None
            return await db_client.db["evidence"].find_one({
                "_id": ObjectId(evidence_id),
                "organization_id": ObjectId(org_id),
            })
        except Exception as e:
            logger.error(f"EvidenceRepository.get_by_id: {e}")
            return None

    @staticmethod
    async def get_by_sha256(case_id: str, sha256: str) -> Optional[Dict[str, Any]]:
        try:
            if not ObjectId.is_valid(case_id):
                return None
            return await db_client.db["evidence"].find_one({
                "case_id": ObjectId(case_id),
                "sha256": sha256,
            })
        except Exception as e:
            logger.error(f"EvidenceRepository.get_by_sha256: {e}")
            return None

    @staticmethod
    async def create(evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        result = await db_client.db["evidence"].insert_one(evidence_data)
        evidence_data["_id"] = result.inserted_id
        return evidence_data

    @staticmethod
    async def list_by_case(case_id: str, org_id: str) -> List[Dict[str, Any]]:
        try:
            if not ObjectId.is_valid(case_id) or not ObjectId.is_valid(org_id):
                return []
            cursor = db_client.db["evidence"].find({
                "case_id": ObjectId(case_id),
                "organization_id": ObjectId(org_id),
            }).sort("created_at", -1)
            return await cursor.to_list(length=100)
        except Exception:
            return []

    @staticmethod
    async def delete(evidence_id: str, org_id: str) -> bool:
        try:
            if not ObjectId.is_valid(evidence_id) or not ObjectId.is_valid(org_id):
                return False
            result = await db_client.db["evidence"].delete_one({
                "_id": ObjectId(evidence_id),
                "organization_id": ObjectId(org_id),
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"EvidenceRepository.delete: {e}")
            return False

    @staticmethod
    async def update_status(
        evidence_id: str,
        org_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            if not ObjectId.is_valid(evidence_id) or not ObjectId.is_valid(org_id):
                return None
            update_fields: Dict[str, Any] = {"status": status}
            if status in ("parsed", "parsing", "queued"):
                update_fields["error_message"] = None
            elif error_message is not None:
                update_fields["error_message"] = error_message
            from pymongo import ReturnDocument
            result = await db_client.db["evidence"].find_one_and_update(
                {"_id": ObjectId(evidence_id), "organization_id": ObjectId(org_id)},
                {"$set": update_fields},
                return_document=ReturnDocument.AFTER,
            )
            return result
        except Exception:
            return None
