"""
Anomaly Context Builder — ForenSight AI
=========================================
Fetches top anomalous events for a case and formats them into a
structured context dict ready for the copilot prompt.
"""

import logging
from typing import Any, Dict, List
from bson import ObjectId
from backend.app.db.mongodb import db_client

logger = logging.getLogger(__name__)


async def build_anomaly_context(
    case: Dict[str, Any], limit: int = 30
) -> List[Dict[str, Any]]:
    """
    Fetch the top anomalous events sorted by anomaly_score descending.

    Parameters
    ----------
    case   : case document from MongoDB (must contain _id and organization_id)
    limit  : max number of anomalies to return

    Returns
    -------
    List of event dicts with string-serialized IDs.
    """
    col = db_client.db["events"]
    cid_obj = ObjectId(str(case["_id"])) if ObjectId.is_valid(str(case["_id"])) else case["_id"]
    oid_obj = ObjectId(str(case["organization_id"])) if ObjectId.is_valid(str(case["organization_id"])) else case["organization_id"]

    base_match = {
        "$or": [
            {"case_id": cid_obj},
            {"case_id": str(case["_id"])},
        ],
        "$and": [
            {"$or": [{"organization_id": oid_obj}, {"organization_id": str(case["organization_id"])}]}
        ]
    }

    cursor = col.find(
        {
            **base_match,
            "is_anomaly": True,
        }
    ).sort("anomaly_score", -1).limit(limit)

    events = await cursor.to_list(length=limit)

    # Fallback: if no events explicitly flagged as is_anomaly, fetch high-severity/key events
    if not events:
        fallback_cursor = col.find(base_match).sort([("severity", -1), ("timestamp", -1)]).limit(limit)
        events = await fallback_cursor.to_list(length=limit)

    for e in events:
        e["id"] = str(e["_id"])
        e["case_id"] = str(e["case_id"])
        e["organization_id"] = str(e["organization_id"])
        e["evidence_id"] = str(e.get("evidence_id", ""))
        # Normalize timestamp for display
        ts = e.get("timestamp")
        if ts and hasattr(ts, "isoformat"):
            e["timestamp"] = ts.isoformat()

    logger.debug(f"Fetched {len(events)} anomalies for case {case['_id']}")
    return events
