"""
Audit Log Repository — ForenSight AI
=====================================
Implements the append-only Merkle-style chain-of-custody audit log described
in Architecture Section 9.

Every mutating API action writes a row here containing:
  - actor (user_id)
  - timestamp
  - action performed
  - target resource (entity_type + entity_id)
  - hash of the *previous* row (Merkle chain link)
  - SHA-256 of the current row payload (self-hash)

This means any tampering with a historical row breaks the hash chain —
exactly the same guarantee as a blockchain without the overhead.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId
from backend.app.db.mongodb import db_client

logger = logging.getLogger(__name__)

COLLECTION = "audit_log"


def _serialize_row(r: dict) -> dict:
    """Convert a raw MongoDB audit document to a JSON-serialisable dict."""
    r = dict(r)
    r["id"]  = str(r.pop("_id", ""))
    # Convert any remaining ObjectId / datetime values
    for k, v in list(r.items()):
        if hasattr(v, "__str__") and type(v).__name__ in ("ObjectId",):
            r[k] = str(v)
        elif hasattr(v, "isoformat"):          # datetime
            r[k] = v.isoformat()
    return r


def _sha256(data: dict) -> str:
    """Deterministic SHA-256 of a dict, sorted keys, UTF-8 encoded."""
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class AuditRepository:

    @staticmethod
    async def _get_last_hash(org_id: str) -> str:
        """
        Fetch the self_hash of the most recent audit row for this org.
        Returns '0' * 64 (genesis hash) if no prior rows exist.
        """
        col = db_client.db[COLLECTION]
        last = await col.find_one(
            {"organization_id": org_id},
            sort=[("created_at", -1)],
            projection={"self_hash": 1}
        )
        return last["self_hash"] if last else ("0" * 64)

    @staticmethod
    async def log(
        actor_id: str,
        org_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Append a new tamper-evident audit entry.

        Parameters
        ----------
        actor_id    : MongoDB user ID performing the action
        org_id      : Organization scope (tenant boundary)
        action      : Human-readable action label, e.g. 'evidence.upload',
                      'case.create', 'case.update', 'graph.clear'
        entity_type : Resource type, e.g. 'evidence', 'case', 'event'
        entity_id   : MongoDB ID of the resource being acted on
        metadata    : Optional extra key-value context (filenames, status
                      changes, etc.) — never store secrets here
        """
        col = db_client.db[COLLECTION]
        now = datetime.utcnow()

        # Step 1 — get hash of the previous row (chain link)
        prev_hash = await AuditRepository._get_last_hash(org_id)

        # Step 2 — build the payload dict (everything except self_hash)
        payload = {
            "actor_id": actor_id,
            "organization_id": org_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "metadata": metadata or {},
            "prev_hash": prev_hash,
            "created_at": now.isoformat(),
        }

        # Step 3 — compute self_hash over the full payload
        self_hash = _sha256(payload)

        # Step 4 — persist (no update ever allowed on this collection)
        doc = {**payload, "created_at": now, "self_hash": self_hash}
        result = await col.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        logger.info(f"[AUDIT] {action} by {actor_id} on {entity_type}:{entity_id}")
        return doc

    @staticmethod
    async def list_for_case(case_id: str, org_id: str, limit: int = 200) -> list:
        col = db_client.db[COLLECTION]
        cursor = col.find(
            {
                "organization_id": org_id,
                "$or": [
                    {"entity_id": case_id},
                    {"metadata.case_id": case_id},
                ],
            },
            sort=[("created_at", 1)],
        ).limit(limit)
        rows = await cursor.to_list(length=limit)
        return [_serialize_row(r) for r in rows]

    @staticmethod
    async def list_for_org(org_id: str, limit: int = 500) -> list:
        """Return the most recent audit entries across all cases for an org."""
        col = db_client.db[COLLECTION]
        cursor = col.find(
            {"organization_id": org_id},
            sort=[("created_at", -1)],
        ).limit(limit)
        rows = await cursor.to_list(length=limit)
        return [_serialize_row(r) for r in rows]

    @staticmethod
    async def verify_chain(org_id: str) -> dict:
        """
        Walk every audit row for an org in insertion order and verify the
        Merkle chain is intact.

        Returns
        -------
        {
          "valid": bool,
          "total": int,
          "broken_at": int | None,   # 1-based row index where chain breaks
          "broken_id": str | None    # _id of the offending row
        }
        """
        col = db_client.db[COLLECTION]
        cursor = col.find(
            {"organization_id": org_id},
            sort=[("created_at", 1)],
        )
        rows = await cursor.to_list(length=10_000)

        prev_hash = "0" * 64
        for i, row in enumerate(rows):
            stored_self = row.get("self_hash", "")
            stored_prev = row.get("prev_hash", "")

            # Verify the chain link
            if stored_prev != prev_hash:
                return {
                    "valid": False,
                    "total": len(rows),
                    "broken_at": i + 1,
                    "broken_id": str(row["_id"]),
                }

            # Re-compute self_hash and verify it matches what was stored
            payload = {
                "actor_id": row.get("actor_id"),
                "organization_id": row.get("organization_id"),
                "action": row.get("action"),
                "entity_type": row.get("entity_type"),
                "entity_id": row.get("entity_id"),
                "metadata": row.get("metadata", {}),
                "prev_hash": stored_prev,
                "created_at": row["created_at"].isoformat()
                if hasattr(row["created_at"], "isoformat")
                else str(row["created_at"]),
            }
            expected = _sha256(payload)
            if expected != stored_self:
                return {
                    "valid": False,
                    "total": len(rows),
                    "broken_at": i + 1,
                    "broken_id": str(row["_id"]),
                }

            prev_hash = stored_self

        return {"valid": True, "total": len(rows), "broken_at": None, "broken_id": None}
