"""
Hash File Parser — ForenSight
===============================
Parses MD5, SHA1, and SHA256 hash list files (.md5, .sha1, .sha256, .txt).
Extracts hashes and associated filenames without misclassifying hashes as malicious.
"""

import re
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional

from backend.app.parsers.base import BaseParser
from backend.app.schemas.event import EventSource, EventType, EventSeverity

logger = logging.getLogger(__name__)

HASH_LINE_PATTERN = re.compile(
    r"^\s*([a-fA-F0-9]{32,64})\s+[\*\s]?(.+)?$"
)


class HashParser(BaseParser):
    def parse(self, file_content: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        events = []
        try:
            text = file_content.decode("utf-8", errors="replace")
            lines = text.splitlines()
            default_ts = datetime.utcnow()

            for line in lines:
                line_str = line.strip()
                if not line_str or line_str.startswith("#"):
                    continue

                match = HASH_LINE_PATTERN.match(line_str)
                if match:
                    hash_val = match.group(1).lower()
                    associated_file = match.group(2).strip() if match.group(2) else "unknown_file"

                    h_type = "md5" if len(hash_val) == 32 else "sha1" if len(hash_val) == 40 else "sha256"

                    event = {
                        "timestamp": default_ts,
                        "event_type": EventType.HASH_RECORD.value,
                        "source": EventSource.TEXT.value,
                        "severity": EventSeverity.INFO.value,
                        "subject": associated_file,
                        "action": "hash_recorded",
                        "object": f"{h_type}:{hash_val}",
                        "file": {
                            "name": associated_file,
                            "path": associated_file,
                            "md5": hash_val if len(hash_val) == 32 else None,
                            "sha1": hash_val if len(hash_val) == 40 else None,
                            "sha256": hash_val if len(hash_val) == 64 else None,
                        },
                        "details": {
                            "hash_type": h_type,
                            "hash_value": hash_val,
                            "associated_file": associated_file,
                        },
                        "mitre_techniques": [],
                        "parser_metadata": {
                            "confidence": 1.0,
                            "extraction_method": "hash_line_regex",
                        },
                    }
                    events.append(event)
        except Exception as e:
            logger.warning(f"Could not parse hash file ({e}).")
        return events
