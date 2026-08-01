"""
Report Repository — ForenSight AI
====================================
Persists generated forensic reports to MongoDB so they can be
retrieved later without re-running the AI pipeline.

Architecture reference: Section 5.4 (Storage Layer) — all facts
must trace back to a persisted record, reports included.
"""

import logging
from datetime import datetime
from typing import Optional, List

from bson import ObjectId
from backend.app.db.mongodb import db_client

logger = logging.getLogger(__name__)

COLLECTION = "reports"


class ReportRepository:

    @staticmethod
    async def create(report_dict: dict) -> dict:
        """Insert a new report document and return it with id set."""
        col = db_client.db[COLLECTION]
        result = await col.insert_one(report_dict)
        report_dict["id"] = str(result.inserted_id)
        return report_dict

    @staticmethod
    async def get_by_id(report_id: str, org_id: str) -> Optional[dict]:
        """Fetch a single report by ID, scoped to the organization."""
        col = db_client.db[COLLECTION]
        if not ObjectId.is_valid(report_id):
            return None
        return await col.find_one({
            "_id": ObjectId(report_id),
            "organization_id": org_id,
        })

    @staticmethod
    async def get_latest_for_case(case_id: str, org_id: str) -> Optional[dict]:
        """Return the most recently generated report for a case."""
        col = db_client.db[COLLECTION]
        return await col.find_one(
            {"case_id": case_id, "organization_id": org_id},
            sort=[("created_at", -1)],
        )

    @staticmethod
    async def list_by_case(case_id: str, org_id: str, limit: int = 20) -> List[dict]:
        """List all reports for a case, newest first."""
        col = db_client.db[COLLECTION]
        cursor = col.find(
            {"case_id": case_id, "organization_id": org_id},
            sort=[("created_at", -1)],
        ).limit(limit)
        rows = await cursor.to_list(length=limit)
        for r in rows:
            r["id"] = str(r["_id"])
        return rows

    @staticmethod
    async def update_pdf_path(report_id: str, org_id: str, minio_path: str) -> bool:
        """Store the MinIO object path after PDF is compiled and uploaded."""
        col = db_client.db[COLLECTION]
        result = await col.update_one(
            {"_id": ObjectId(report_id), "organization_id": org_id},
            {"$set": {"pdf_minio_path": minio_path, "updated_at": datetime.utcnow()}},
        )
        return result.modified_count > 0

    @staticmethod
    async def delete(report_id: str, org_id: str) -> bool:
        """Delete a report document (e.g. when regenerating)."""
        col = db_client.db[COLLECTION]
        result = await col.delete_one({
            "_id": ObjectId(report_id),
            "organization_id": org_id,
        })
        return result.deleted_count > 0
