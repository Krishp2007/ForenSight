import re
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional

from backend.app.parsers.base import BaseParser
from backend.app.parsers.extractor import EntityRelationshipExtractor
from backend.app.schemas.event import EventSource, EventType, EventSeverity

logger = logging.getLogger(__name__)

# Pre-compiled high performance non-backtracking Regex Extractors
IP_V4_RE = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
URL_RE   = re.compile(r"https?://[^\s\"'>]+")
PATH_RE  = re.compile(r"(?:[a-zA-Z]:\\[^:\*\?\"<>\|\r\n]+|/[a-zA-Z0-9_\-\./]+)")
HASH_RE  = re.compile(r"\b[a-fA-F0-9]{32,64}\b")
USER_RE  = re.compile(r"\b(?:user|username|account)\s*[:=]\s*([a-zA-Z0-9_\-\.\\]+)\b", re.IGNORECASE)


class TextParser(BaseParser):
    def parse(self, file_content: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        now = datetime.utcnow()

        try:
            text = file_content.decode("utf-8", errors="replace")
        except Exception:
            text = file_content.decode("latin-1", errors="replace")

        for lineno, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            # Extract deterministic patterns from raw text line
            ip_match = IP_V4_RE.search(line)
            url_match = URL_RE.search(line)
            path_match = PATH_RE.search(line)
            hash_match = HASH_RE.search(line)
            user_match = USER_RE.search(line)

            ip_val = ip_match.group(0) if ip_match else None
            url_val = url_match.group(0) if url_match else None
            path_val = path_match.group(0) if path_match else None
            hash_val = hash_match.group(0) if hash_match else None
            user_val = user_match.group(1) if user_match else None

            severity = EventSeverity.INFO.value
            if "error" in line.lower() or "fail" in line.lower() or "denied" in line.lower():
                severity = EventSeverity.MEDIUM.value

            base_event = {
                "source_file": filename or "log_file",
                "source_type": EventSource.TEXT.value,
                "timestamp": now,
                "event_type": EventType.GENERIC.value,
                "event_category": "unstructured_log",
                "severity": severity,

                "host": {"hostname": "LogHost", "ip": ip_val, "os": None},
                "user": {"username": user_val, "domain": None, "sid": None},
                "process": {"pid": None, "ppid": None, "name": None, "path": path_val, "command_line": None, "hash": hash_val},
                "parent_process": {"pid": None, "name": None, "path": None, "command_line": None},
                "file": {"name": path_val, "path": path_val, "extension": None, "size": None, "md5": hash_val if hash_val and len(hash_val) == 32 else None, "sha1": None, "sha256": hash_val if hash_val and len(hash_val) == 64 else None},
                "network": {
                    "source_ip": ip_val, "source_port": None,
                    "destination_ip": None, "destination_port": None,
                    "protocol": "TCP", "domain": None, "dns_query": None, "url": url_val, "direction": None
                },
                "registry": {"key": None, "value_name": None, "value_data": None, "operation": None},
                "service": {"name": None, "display_name": None, "binary_path": None, "start_type": None},
                "authentication": {"logon_type": None, "source_ip": ip_val, "status": None, "failure_reason": None},

                "subject": filename or "text_file",
                "action": "log_entry",
                "object": line[:200],
                "details": {
                    "raw_line": raw_line,
                    "line_number": lineno,
                    "extracted_ip": ip_val,
                    "extracted_url": url_val,
                    "extracted_path": path_val,
                    "extracted_hash": hash_val,
                },
                "raw_event": {"raw_line": raw_line},
                "mitre_techniques": [],
                "parser_metadata": {
                    "confidence": 0.85,
                    "extraction_method": "precompiled_regex_patterns",
                },
            }

            extracted = EntityRelationshipExtractor.extract_from_event(base_event)
            base_event["entities"] = extracted["entities"]
            base_event["relationships"] = extracted["relationships"]

            events.append(base_event)

        if not events:
            events.append({
                "timestamp": now,
                "event_type": EventType.GENERIC.value,
                "source": EventSource.TEXT.value,
                "severity": EventSeverity.INFO.value,
                "subject": filename or "text_file",
                "action": "file_ingested",
                "object": filename or "unknown",
                "details": {"file_size": len(file_content)},
                "mitre_techniques": [],
            })

        return events
