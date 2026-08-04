import logging
from typing import Optional, Dict, Any, List
from bson import ObjectId
from backend.app.db.mongodb import db_client

logger = logging.getLogger(__name__)

class EvidenceRepository:
    @staticmethod
    async def get_by_id(evidence_id: str, org_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve evidence scoped by organization ID."""
        try:
            if not ObjectId.is_valid(evidence_id) or not ObjectId.is_valid(org_id):
                return None
            return await db_client.db["evidence"].find_one({
                "_id": ObjectId(evidence_id),
                "organization_id": ObjectId(org_id)
            })
        except Exception as e:
            logger.error(f"Error in EvidenceRepository.get_by_id: {e}")
            return None

    @staticmethod
    async def get_by_sha256(case_id: str, sha256: str) -> Optional[Dict[str, Any]]:
        """Check if file with exact SHA256 has already been uploaded in case context."""
        try:
            if not ObjectId.is_valid(case_id):
                return None
            return await db_client.db["evidence"].find_one({
                "case_id": ObjectId(case_id),
                "sha256": sha256
            })
        except Exception as e:
            logger.error(f"Error in EvidenceRepository.get_by_sha256: {e}")
            return None

    @staticmethod
    async def create(evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new evidence document into MongoDB."""
        result = await db_client.db["evidence"].insert_one(evidence_data)
        evidence_data["_id"] = result.inserted_id
        return evidence_data

    @staticmethod
    async def list_by_case(case_id: str, org_id: str) -> List[Dict[str, Any]]:
        """List all evidence attached to a case, scoped by organization ID."""
        try:
            if not ObjectId.is_valid(case_id) or not ObjectId.is_valid(org_id):
                return []
            cursor = db_client.db["evidence"].find({
                "case_id": ObjectId(case_id),
                "organization_id": ObjectId(org_id)
            })
            return await cursor.to_list(length=100)
        except Exception:
            return []

    @staticmethod
    async def update_status(
        evidence_id: str,
        org_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update the processing status and error message of an evidence document."""
        try:
            if not ObjectId.is_valid(evidence_id) or not ObjectId.is_valid(org_id):
                return None
                
            update_fields = {"status": status}
            if error_message is not None:
                update_fields["error_message"] = error_message
                
            result = await db_client.db["evidence"].find_one_and_update(
                {"_id": ObjectId(evidence_id), "organization_id": ObjectId(org_id)},
                {"$set": update_fields},
                return_document=True
            )
            return result
        except Exception:
            return None

    @staticmethod
    async def delete(evidence_id: str, org_id: str) -> bool:
        """Scope specific deletion of evidence by organization ID."""
        try:
            if not ObjectId.is_valid(evidence_id) or not ObjectId.is_valid(org_id):
                return False
            result = await db_client.db["evidence"].delete_one({
                "_id": ObjectId(evidence_id),
                "organization_id": ObjectId(org_id)
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error in EvidenceRepository.delete: {e}")
            return False
