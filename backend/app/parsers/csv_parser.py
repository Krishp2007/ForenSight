import io
import csv
from datetime import datetime
from functools import lru_cache
import logging
from typing import List, Dict, Any, Optional

from backend.app.parsers.base import BaseParser
from backend.app.schemas.event import EventSource, EventType, EventSeverity

logger = logging.getLogger(__name__)

# Build valid-value sets once at import time — not per row
_VALID_SEVERITY   = frozenset(s.value for s in EventSeverity)
_VALID_EVENT_TYPE = frozenset(t.value for t in EventType)

# Timestamp formats tried in order (most common first)
_TS_FORMATS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S",
)


@lru_cache(maxsize=2048)
def _parse_ts_cached(ts_val: str) -> Optional[datetime]:
    """Parse a timestamp string, cached so repeated identical values cost nothing."""
    s = ts_val.strip()
    for fmt in _TS_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


class CsvParser(BaseParser):
    def parse(self, file_content: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        events = []
        try:
            text_data = file_content.decode('utf-8', errors='replace')
            reader    = csv.DictReader(io.StringIO(text_data))
            headers   = reader.fieldnames or []
            headers_lower = [h.lower() for h in headers]
            col_map   = self._detect_columns(headers_lower, headers)

            default_ts = datetime.utcnow()
            for row in reader:
                event_dict = self._parse_row(row, col_map, filename, default_ts)
                if event_dict:
                    events.append(event_dict)

        except Exception as e:
            logger.warning(f"Could not parse CSV ({e}). Using fallback.")
            events.append({
                "timestamp":       datetime.utcnow(),
                "event_type":      EventType.CSV.value,
                "source":          EventSource.CSV.value,
                "severity":        EventSeverity.INFO.value,
                "subject":         "CsvParser",
                "action":          "parsed_fallback",
                "object":          filename or "unknown_csv_file",
                "details":         {"raw_fallback": True, "file_size": len(file_content)},
                "mitre_techniques": [],
            })
        return events

    def _detect_columns(self, headers_lower: List[str], original_headers: List[str]) -> Dict[str, str]:
        mapping: Dict[str, Optional[str]] = {}

        def find_match(keywords):
            for kw in keywords:
                if kw in headers_lower:
                    return original_headers[headers_lower.index(kw)]
            return None

        mapping["timestamp"]  = find_match(["timestamp", "time", "datetime", "date", "created"])
        mapping["event_type"] = find_match(["event_type", "type", "category", "event"])
        mapping["subject"]    = find_match(["subject", "actor", "user", "source_name"])
        mapping["action"]     = find_match(["action", "operation", "event_id"])
        mapping["object"]     = find_match(["object", "target", "path", "destination"])
        mapping["severity"]   = find_match(["severity", "level", "priority"])
        return mapping

    def _parse_row(
        self,
        row: Dict[str, str],
        col_map: Dict[str, str],
        filename: Optional[str],
        default_ts: datetime,
    ) -> Optional[Dict[str, Any]]:
        try:
            # Timestamp — use cache so identical strings cost one lookup
            ts_col = col_map.get("timestamp")
            ts_val = row.get(ts_col) if ts_col else None
            timestamp = (_parse_ts_cached(ts_val) or default_ts) if ts_val else default_ts

            # Subject
            subj_col = col_map.get("subject")
            subj = (row.get(subj_col) if subj_col else None) or (
                next(iter(row.values()), "UnknownSubject")
            )

            # Action
            act_col = col_map.get("action")
            act = (row.get(act_col) if act_col else None) or "occurred"

            # Object
            obj_col = col_map.get("object")
            obj = (row.get(obj_col) if obj_col else None)
            if not obj:
                keys = list(row.keys())
                obj = row.get(keys[1]) if len(keys) > 1 else (filename or "unknown_resource")

            # Severity — frozenset lookup is O(1)
            sev_col = col_map.get("severity")
            sev_raw = (row.get(sev_col) or "info") if sev_col else "info"
            severity = sev_raw.strip().lower() if sev_raw.strip().lower() in _VALID_SEVERITY else EventSeverity.INFO.value

            # Event type
            type_col = col_map.get("event_type")
            type_raw = (row.get(type_col) or "generic") if type_col else "generic"
            event_type = type_raw.strip().lower() if type_raw.strip().lower() in _VALID_EVENT_TYPE else EventType.GENERIC.value

            return {
                "timestamp":        timestamp,
                "event_type":       event_type,
                "source":           EventSource.CSV.value,
                "severity":         severity,
                "subject":          str(subj),
                "action":           str(act),
                "object":           str(obj),
                "details":          dict(row),
                "mitre_techniques": [],
            }
        except Exception:
            return None
