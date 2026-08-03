import json
from datetime import datetime
from functools import lru_cache
import logging
from typing import List, Dict, Any, Optional

from backend.app.parsers.base import BaseParser
from backend.app.schemas.event import EventSource, EventType, EventSeverity

logger = logging.getLogger(__name__)

_VALID_SEVERITY   = frozenset(s.value for s in EventSeverity)
_VALID_EVENT_TYPE = frozenset(t.value for t in EventType)

_TS_FORMATS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S",
)


@lru_cache(maxsize=2048)
def _parse_ts_cached(ts_val: str) -> Optional[datetime]:
    s = ts_val.strip()
    for fmt in _TS_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


class JsonParser(BaseParser):
    def parse(self, file_content: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        events = []
        try:
            data = json.loads(file_content.decode('utf-8', errors='replace'))
            items = data if isinstance(data, list) else ([data] if isinstance(data, dict) else [])
            default_ts = datetime.utcnow()
            for item in items:
                if isinstance(item, dict):
                    ev = self._parse_item(item, filename, default_ts)
                    if ev:
                        events.append(ev)
        except Exception as e:
            logger.warning(f"Could not parse JSON ({e}). Using fallback.")
            events.append({
                "timestamp":       datetime.utcnow(),
                "event_type":      EventType.JSON.value,
                "source":          EventSource.JSON.value,
                "severity":        EventSeverity.INFO.value,
                "subject":         "JsonParser",
                "action":          "parsed_fallback",
                "object":          filename or "unknown_json_file",
                "details":         {"raw_fallback": True, "file_size": len(file_content)},
                "mitre_techniques": [],
            })
        return events

    def _parse_item(self, item: Dict[str, Any], filename: Optional[str], default_ts: datetime) -> Optional[Dict[str, Any]]:
        try:
            ts_val = item.get("timestamp") or item.get("time") or item.get("datetime")
            timestamp = default_ts
            if ts_val:
                parsed = _parse_ts_cached(str(ts_val))
                if parsed:
                    timestamp = parsed

            subj = item.get("subject") or item.get("actor") or item.get("user") or "System"
            act  = item.get("action")  or item.get("operation") or "occurred"
            obj  = item.get("object")  or item.get("target")    or item.get("path") or filename or "unknown_resource"

            sev_raw  = str(item.get("severity") or item.get("level") or "info").lower().strip()
            severity = sev_raw if sev_raw in _VALID_SEVERITY else EventSeverity.INFO.value

            type_raw   = str(item.get("event_type") or item.get("type") or "generic").lower().strip()
            event_type = type_raw if type_raw in _VALID_EVENT_TYPE else EventType.GENERIC.value

            mitre = item.get("mitre_techniques") or item.get("techniques") or []
            if not isinstance(mitre, list):
                mitre = []

            # Truncate details to keep MongoDB storage minimal
            clean_details = {}
            if isinstance(item, dict):
                for k, v in item.items():
                    if isinstance(v, str) and len(v) > 300:
                        clean_details[k] = v[:300] + "... [truncated]"
                    elif not isinstance(v, (dict, list)) or len(str(v)) < 1000:
                        clean_details[k] = v

            return {
                "timestamp":        timestamp,
                "event_type":       event_type,
                "source":           EventSource.JSON.value,
                "severity":         severity,
                "subject":          str(subj)[:150],
                "action":           str(act)[:150],
                "object":           str(obj)[:250],
                "details":          clean_details,
                "mitre_techniques": [str(t) for t in mitre],
            }
        except Exception:
            return None
