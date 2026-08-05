import logging
from typing import Optional, Dict, Any, List
from bson import ObjectId
from backend.app.db.mongodb import db_client

logger = logging.getLogger(__name__)


class EvidenceRepository:

    @staticmethod
    async def _sanitize_legacy_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not doc:
            return doc
        status = doc.get("status")
        if status in ("parsed", "failed") and doc.get("scan_duration_ms") is None:
            created = doc.get("created_at")
            updated = doc.get("updated_at") or doc.get("parsed_at") or doc.get("processing_finished_at")
            duration_ms = 2000  # Default fallback 2s
            if created and updated and hasattr(created, "timestamp") and hasattr(updated, "timestamp"):
                diff_s = updated.timestamp() - created.timestamp()
                if 0 < diff_s < 1800:
                    duration_ms = int(diff_s * 1000)
            duration_ms = max(1000, duration_ms)
            doc["scan_duration_ms"] = duration_ms
            try:
                await db_client.db["evidence"].update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"scan_duration_ms": duration_ms}}
                )
            except Exception:
                pass
        return doc

    @staticmethod
    async def get_by_id(evidence_id: str, org_id: str) -> Optional[Dict[str, Any]]:
        try:
            if not ObjectId.is_valid(evidence_id) or not ObjectId.is_valid(org_id):
                return None
            doc = await db_client.db["evidence"].find_one({
                "_id": ObjectId(evidence_id),
                "organization_id": ObjectId(org_id),
            })
            return await EvidenceRepository._sanitize_legacy_doc(doc)
        except Exception as e:
            logger.error(f"EvidenceRepository.get_by_id: {e}")
            return None

    @staticmethod
    async def get_by_sha256(case_id: str, sha256: str) -> Optional[Dict[str, Any]]:
        try:
            if not ObjectId.is_valid(case_id):
                return None
            doc = await db_client.db["evidence"].find_one({
                "case_id": ObjectId(case_id),
                "sha256": sha256,
            })
            return await EvidenceRepository._sanitize_legacy_doc(doc)
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
            docs = await cursor.to_list(length=100)
            sanitized = []
            for doc in docs:
                sanitized.append(await EvidenceRepository._sanitize_legacy_doc(doc))
            return sanitized
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
        scan_duration_ms: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            if not ObjectId.is_valid(evidence_id) or not ObjectId.is_valid(org_id):
                return None
            from datetime import datetime
            now = datetime.utcnow()
            update_fields: Dict[str, Any] = {"status": status, "updated_at": now}

            if status in ("parsed", "parsing", "queued", "uploaded"):
                update_fields["error_message"] = None
            elif error_message is not None:
                update_fields["error_message"] = error_message

            # When starting parsing or re-processing:
            if status == "parsing":
                update_fields["processing_started_at"] = now
                update_fields["parsing_started_at"] = now
                update_fields["processing_finished_at"] = None
                update_fields["parsed_at"] = None
                update_fields["scan_duration_ms"] = None

            # When terminal state reached (parsed or failed):
            elif status in ("parsed", "failed"):
                update_fields["processing_finished_at"] = now
                update_fields["parsed_at"] = now

                if scan_duration_ms is not None:
                    update_fields["scan_duration_ms"] = int(scan_duration_ms)
                else:
                    # Fetch existing record to calculate delta against processing_started_at
                    doc = await db_client.db["evidence"].find_one({"_id": ObjectId(evidence_id)})
                    if doc:
                        start_time = doc.get("processing_started_at") or doc.get("parsing_started_at")
                        if start_time and isinstance(start_time, datetime):
                            delta_ms = int((now - start_time).total_seconds() * 1000)
                            update_fields["scan_duration_ms"] = max(0, delta_ms)

            from pymongo import ReturnDocument
            result = await db_client.db["evidence"].find_one_and_update(
                {"_id": ObjectId(evidence_id), "organization_id": ObjectId(org_id)},
                {"$set": update_fields},
                return_document=ReturnDocument.AFTER,
            )
            return result
        except Exception as e:
            logger.error(f"EvidenceRepository.update_status error: {e}")
            return None
