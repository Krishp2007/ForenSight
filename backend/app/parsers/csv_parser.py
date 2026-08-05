import io
import csv
from datetime import datetime
from functools import lru_cache
import logging
from typing import List, Dict, Any, Optional

from backend.app.parsers.base import BaseParser
from backend.app.parsers.extractor import EntityRelationshipExtractor
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
                "timestamp": datetime.utcnow(),
                "event_type": EventType.CSV.value,
                "source": EventSource.CSV.value,
                "severity": EventSeverity.INFO.value,
                "subject": "CsvParser",
                "action": "parsed_fallback",
                "object": filename or "unknown_csv_file",
                "details": {"raw_fallback": True, "file_size": len(file_content)},
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

        mapping["timestamp"]   = find_match(["timestamp", "time", "datetime", "date", "created"])
        mapping["event_type"]  = find_match(["event_type", "type", "category", "event"])
        mapping["subject"]     = find_match(["subject", "actor", "user", "username", "source_name"])
        mapping["action"]      = find_match(["action", "operation", "event_id"])
        mapping["object"]      = find_match(["object", "target", "path", "destination"])
        mapping["severity"]    = find_match(["severity", "level", "priority"])
        mapping["src_ip"]      = find_match(["src_ip", "source_ip", "source ip", "client_ip"])
        mapping["dst_ip"]      = find_match(["dst_ip", "destination_ip", "destination ip", "dest_ip"])
        mapping["src_port"]    = find_match(["src_port", "source_port", "source port"])
        mapping["dst_port"]    = find_match(["dst_port", "destination_port", "destination port"])
        mapping["pid"]         = find_match(["pid", "process_id", "process id"])
        mapping["ppid"]        = find_match(["ppid", "parent_process_id", "parent process id"])
        mapping["process_name"]= find_match(["process", "process_name", "process name", "exe"])
        mapping["cmd_line"]    = find_match(["command_line", "cmdline", "command line"])
        mapping["filepath"]    = find_match(["file_path", "filepath", "path", "filename"])

        return mapping

    def _parse_row(
        self,
        row: Dict[str, str],
        col_map: Dict[str, str],
        filename: Optional[str],
        default_ts: datetime,
    ) -> Optional[Dict[str, Any]]:
        try:
            ts_col = col_map.get("timestamp")
            ts_val = row.get(ts_col) if ts_col else None
            timestamp = (_parse_ts_cached(ts_val) or default_ts) if ts_val else default_ts

            subj_col = col_map.get("subject")
            subj = (row.get(subj_col) if subj_col else None) or (
                next(iter(row.values()), "UnknownSubject")
            )

            act_col = col_map.get("action")
            act = (row.get(act_col) if act_col else None) or "occurred"

            obj_col = col_map.get("object")
            obj = (row.get(obj_col) if obj_col else None)
            if not obj:
                keys = list(row.keys())
                obj = row.get(keys[1]) if len(keys) > 1 else (filename or "unknown_resource")

            sev_col = col_map.get("severity")
            sev_raw = (row.get(sev_col) or "info") if sev_col else "info"
            severity = sev_raw.strip().lower() if sev_raw.strip().lower() in _VALID_SEVERITY else EventSeverity.INFO.value

            type_col = col_map.get("event_type")
            type_raw = (row.get(type_col) or "generic") if type_col else "generic"
            event_type = type_raw.strip().lower() if type_raw.strip().lower() in _VALID_EVENT_TYPE else EventType.GENERIC.value

            # Extract normalized objects from row alias map
            src_ip = row.get(col_map.get("src_ip")) if col_map.get("src_ip") else None
            dst_ip = row.get(col_map.get("dst_ip")) if col_map.get("dst_ip") else None
            src_port = int(row.get(col_map.get("src_port"))) if col_map.get("src_port") and str(row.get(col_map.get("src_port"))).isdigit() else None
            dst_port = int(row.get(col_map.get("dst_port"))) if col_map.get("dst_port") and str(row.get(col_map.get("dst_port"))).isdigit() else None

            pid = int(row.get(col_map.get("pid"))) if col_map.get("pid") and str(row.get(col_map.get("pid"))).isdigit() else None
            ppid = int(row.get(col_map.get("ppid"))) if col_map.get("ppid") and str(row.get(col_map.get("ppid"))).isdigit() else None
            proc_name = row.get(col_map.get("process_name")) if col_map.get("process_name") else None
            cmd_line = row.get(col_map.get("cmd_line")) if col_map.get("cmd_line") else None
            filepath = row.get(col_map.get("filepath")) if col_map.get("filepath") else None

            base_event = {
                "source_file": filename or "csv_file",
                "source_type": EventSource.CSV.value,
                "timestamp": timestamp,
                "event_type": event_type,
                "event_category": "structured_csv",
                "severity": severity,

                "host": {"hostname": "CSVHost", "ip": src_ip, "os": None},
                "user": {"username": str(subj) if subj else None, "domain": None, "sid": None},
                "process": {"pid": pid, "ppid": ppid, "name": proc_name, "path": filepath, "command_line": cmd_line, "hash": None},
                "parent_process": {"pid": ppid, "name": None, "path": None, "command_line": None},
                "file": {"name": filepath, "path": filepath, "extension": None, "size": None, "md5": None, "sha1": None, "sha256": None},
                "network": {
                    "source_ip": src_ip, "source_port": src_port,
                    "destination_ip": dst_ip, "destination_port": dst_port,
                    "protocol": "TCP", "domain": None, "dns_query": None, "url": None, "direction": None
                },
                "registry": {"key": None, "value_name": None, "value_data": None, "operation": None},
                "service": {"name": None, "display_name": None, "binary_path": None, "start_type": None},
                "authentication": {"logon_type": None, "source_ip": src_ip, "status": None, "failure_reason": None},

                "subject": str(subj),
                "action": str(act),
                "object": str(obj),
                "details": dict(row),
                "raw_event": dict(row),
                "mitre_techniques": [],
                "parser_metadata": {
                    "confidence": 0.9,
                    "extraction_method": "csv_alias_map",
                },
            }

            extracted = EntityRelationshipExtractor.extract_from_event(base_event)
            base_event["entities"] = extracted["entities"]
            base_event["relationships"] = extracted["relationships"]

            return base_event
        except Exception:
            return None
