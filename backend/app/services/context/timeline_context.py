"""
Timeline Context Builder — ForenSight AI
=========================================
Fetches a chronological slice of events and groups them into
activity bursts (sessions) for the copilot and report.
Architecture Section 5.5.1 — clustering of filesystem events into sessions.
"""

import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional
from bson import ObjectId
from backend.app.db.mongodb import db_client

logger = logging.getLogger(__name__)

SESSION_GAP_MINUTES = 15  # Events more than 15 min apart start a new session


async def build_timeline_context(
    case: Dict[str, Any],
    severity: Optional[str] = None,
    limit: int = 200,
) -> Dict[str, Any]:
    """
    Fetch chronological events and group them into activity sessions.

    Parameters
    ----------
    case     : case document (must have _id, organization_id)
    severity : optional filter ('high', 'critical', etc.)
    limit    : max events to fetch

    Returns
    -------
    {
      "events"  : [EventDict, ...],
      "sessions": [{"start": ts, "end": ts, "count": int, "events": [...]}],
      "total"   : int,
      "span_hours": float
    }
    """
    col = db_client.db["events"]
    cid_obj = ObjectId(str(case["_id"])) if ObjectId.is_valid(str(case["_id"])) else case["_id"]
    query: Dict[str, Any] = {
        "$or": [
            {"case_id": cid_obj},
            {"case_id": str(case["_id"])},
        ]
    }
    if severity:
        query["severity"] = severity

    cursor = col.find(query).sort("timestamp", 1).limit(limit)
    events = await cursor.to_list(length=limit)

    def _to_dt(val):
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            try: return datetime.fromisoformat(val.replace("Z", "+00:00"))
            except Exception: pass
        return None

    for e in events:
        e["id"] = str(e["_id"])
        e["case_id"] = str(e["case_id"])
        e["organization_id"] = str(e["organization_id"])
        e["evidence_id"] = str(e.get("evidence_id", ""))
        ts_dt = _to_dt(e.get("timestamp"))
        if ts_dt:
            e["timestamp"] = ts_dt
            e["timestamp_str"] = ts_dt.isoformat()

    # Group into sessions by time gap
    sessions: List[Dict[str, Any]] = []
    if events:
        session: Dict[str, Any] = {
            "start": events[0].get("timestamp"),
            "end": events[0].get("timestamp"),
            "count": 1,
            "events": [events[0]],
        }
        for ev in events[1:]:
            ts = ev.get("timestamp")
            prev_ts = session["end"]
            if isinstance(ts, datetime) and isinstance(prev_ts, datetime) and (ts - prev_ts) > timedelta(minutes=SESSION_GAP_MINUTES):
                sessions.append(session)
                session = {"start": ts, "end": ts, "count": 1, "events": [ev]}
            else:
                session["end"] = ts
                session["count"] += 1
                session["events"].append(ev)
        sessions.append(session)

    # Compute total span
    span_hours = 0.0
    if events:
        first = events[0].get("timestamp")
        last = events[-1].get("timestamp")
        if isinstance(first, datetime) and isinstance(last, datetime):
            try:
                span_hours = round((last - first).total_seconds() / 3600, 2)
            except Exception:
                pass

    logger.debug(
        f"Timeline: {len(events)} events → {len(sessions)} sessions "
        f"spanning {span_hours}h for case {case['_id']}"
    )
    return {
        "events": events,
        "sessions": sessions,
        "total": len(events),
        "span_hours": span_hours,
    }
