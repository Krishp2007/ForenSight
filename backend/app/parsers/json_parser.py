import json
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


class JsonParser(BaseParser):
    def parse(self, file_content: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        events = []
        default_ts = datetime.utcnow()
        try:
            text = file_content.decode('utf-8', errors='replace').strip()
            # Support single JSON, JSON Array, and NDJSON (JSON Lines)
            items = []
            if text.startswith("[") and text.endswith("]"):
                items = json.loads(text)
            elif text.startswith("{") and text.endswith("}"):
                items = [json.loads(text)]
            else:
                for line in text.splitlines():
                    l = line.strip()
                    if l and l.startswith("{"):
                        try:
                            items.append(json.loads(l))
                        except Exception:
                            pass

            for item in items:
                if isinstance(item, dict):
                    ev = self._parse_item(item, filename, default_ts)
                    if ev:
                        events.append(ev)

        except Exception as e:
            logger.warning(f"Could not parse JSON ({e}). Using fallback.")
            events.append({
                "timestamp": datetime.utcnow(),
                "event_type": EventType.JSON.value,
                "source": EventSource.JSON.value,
                "severity": EventSeverity.INFO.value,
                "subject": "JsonParser",
                "action": "parsed_fallback",
                "object": filename or "unknown_json_file",
                "details": {"raw_fallback": True, "file_size": len(file_content)},
                "mitre_techniques": [],
            })
        return events

    def _parse_item(self, item: Dict[str, Any], filename: Optional[str], default_ts: datetime) -> Optional[Dict[str, Any]]:
        try:
            ts_val = item.get("timestamp") or item.get("time") or item.get("datetime")
            timestamp = (_parse_ts_cached(str(ts_val)) or default_ts) if ts_val else default_ts

            subj = item.get("subject") or item.get("actor") or item.get("user") or item.get("username") or "System"
            act  = item.get("action")  or item.get("operation") or "occurred"
            obj  = item.get("object")  or item.get("target")    or item.get("path") or filename or "unknown_resource"

            sev_raw  = str(item.get("severity") or item.get("level") or "info").lower().strip()
            severity = sev_raw if sev_raw in _VALID_SEVERITY else EventSeverity.INFO.value

            type_raw   = str(item.get("event_type") or item.get("type") or "generic").lower().strip()
            event_type = type_raw if type_raw in _VALID_EVENT_TYPE else EventType.GENERIC.value

            mitre = item.get("mitre_techniques") or item.get("techniques") or []
            if not isinstance(mitre, list):
                mitre = []

            proc = item.get("process", {}) if isinstance(item.get("process"), dict) else {}
            net = item.get("network", {}) if isinstance(item.get("network"), dict) else {}
            user = item.get("user", {}) if isinstance(item.get("user"), dict) else {}
            host = item.get("host", {}) if isinstance(item.get("host"), dict) else {}

            base_event = {
                "source_file": filename or "json_file",
                "source_type": EventSource.JSON.value,
                "timestamp": timestamp,
                "event_type": event_type,
                "event_category": "structured_json",
                "severity": severity,

                "host": {
                    "hostname": host.get("hostname") or item.get("hostname") or item.get("host"),
                    "ip": host.get("ip") or item.get("ip"),
                    "os": host.get("os"),
                },
                "user": {
                    "username": user.get("username") or item.get("username") or (subj if isinstance(subj, str) else None),
                    "domain": user.get("domain") or item.get("domain"),
                    "sid": user.get("sid"),
                },
                "process": {
                    "pid": proc.get("pid") or item.get("pid"),
                    "ppid": proc.get("ppid") or item.get("ppid"),
                    "name": proc.get("name") or item.get("process_name"),
                    "path": proc.get("path") or item.get("path"),
                    "command_line": proc.get("command_line") or item.get("cmdline"),
                    "hash": proc.get("hash") or item.get("sha256"),
                },
                "parent_process": {
                    "pid": item.get("ppid"),
                    "name": item.get("parent_process"),
                    "path": None,
                    "command_line": None,
                },
                "file": {
                    "name": item.get("filename"),
                    "path": item.get("filepath") or item.get("path"),
                    "extension": None,
                    "size": item.get("size"),
                    "md5": item.get("md5"),
                    "sha1": item.get("sha1"),
                    "sha256": item.get("sha256"),
                },
                "network": {
                    "source_ip": net.get("source_ip") or item.get("src_ip"),
                    "source_port": net.get("source_port") or item.get("src_port"),
                    "destination_ip": net.get("destination_ip") or item.get("dst_ip"),
                    "destination_port": net.get("destination_port") or item.get("dst_port"),
                    "protocol": net.get("protocol") or item.get("protocol") or "TCP",
                    "domain": net.get("domain") or item.get("domain"),
                    "dns_query": net.get("dns_query"),
                    "url": net.get("url") or item.get("url"),
                    "direction": net.get("direction"),
                },
                "registry": {"key": item.get("registry_key"), "value_name": None, "value_data": None, "operation": None},
                "service": {"name": item.get("service_name"), "display_name": None, "binary_path": None, "start_type": None},
                "authentication": {"logon_type": None, "source_ip": item.get("src_ip"), "status": None, "failure_reason": None},

                "subject": str(subj)[:150],
                "action": str(act)[:150],
                "object": str(obj)[:250],
                "details": dict(item),
                "raw_event": dict(item),
                "mitre_techniques": [str(t) for t in mitre],
                "parser_metadata": {
                    "confidence": 1.0,
                    "extraction_method": "json_parser",
                },
            }

            extracted = EntityRelationshipExtractor.extract_from_event(base_event)
            base_event["entities"] = extracted["entities"]
            base_event["relationships"] = extracted["relationships"]

            return base_event
        except Exception:
            return None
