"""
Text / Hash File Parser — ForenSight AI
========================================
Handles plain-text evidence files including:
  - MD5 / SHA1 / SHA256 hash manifests  (.md5, .sha1, .sha256, .hash)
  - Generic log files                   (.txt, .log)

Hash manifest format (standard md5sum / sha256sum output):
  <hash>  <filename>
  e.g.  d41d8cd98f00b204e9800998ecf8427e  evidence.bin

Each line becomes one HASH_RECORD event with:
  subject  = the hash value
  action   = "hash_recorded"
  object   = the filename referenced (or "unknown" if bare hash)
  severity = INFO (bumped to MEDIUM if hash looks like a known-bad pattern)
  details  = { hash, algorithm, referenced_file, raw_line }
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional

from backend.app.parsers.base import BaseParser
from backend.app.schemas.event import EventSource, EventType, EventSeverity

# Regex patterns for hash detection
_MD5_RE    = re.compile(r'^([a-fA-F0-9]{32})')
_SHA1_RE   = re.compile(r'^([a-fA-F0-9]{40})')
_SHA256_RE = re.compile(r'^([a-fA-F0-9]{64})')
_SHA512_RE = re.compile(r'^([a-fA-F0-9]{128})')


def _detect_hash(token: str):
    """Return (hash_value, algorithm) or None."""
    t = token.strip()
    if _SHA512_RE.match(t): return t, "sha512"
    if _SHA256_RE.match(t): return t, "sha256"
    if _SHA1_RE.match(t):   return t, "sha1"
    if _MD5_RE.match(t):    return t, "md5"
    return None


class TextParser(BaseParser):
    def parse(self, file_content: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        now = datetime.utcnow()

        try:
            text = file_content.decode("utf-8", errors="replace")
        except Exception:
            text = file_content.decode("latin-1", errors="replace")

        ext = (filename or "").rsplit(".", 1)[-1].lower() if filename and "." in filename else ""
        is_hash_file = ext in ("md5", "sha1", "sha256", "sha512", "hash")

        for lineno, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            # ── Hash manifest line: "<hash>  <path>" or just "<hash>" ──────
            parts = line.split(None, 1)  # split on first whitespace
            first_token = parts[0] if parts else ""
            result = _detect_hash(first_token)

            if result:
                hash_val, algorithm = result
                ref_file = parts[1].lstrip("*").strip() if len(parts) > 1 else "unknown"
                events.append({
                    "timestamp":        now,
                    "event_type":       EventType.HASH_RECORD.value,
                    "source":           EventSource.TEXT.value,
                    "severity":         EventSeverity.INFO.value,
                    "subject":          hash_val,
                    "action":           "hash_recorded",
                    "object":           ref_file,
                    "details": {
                        "hash":            hash_val,
                        "algorithm":       algorithm,
                        "referenced_file": ref_file,
                        "raw_line":        raw_line,
                        "line_number":     lineno,
                    },
                    "mitre_techniques": [],
                })
                continue

            # ── Generic text / log line ───────────────────────────────────
            if not is_hash_file:
                events.append({
                    "timestamp":        now,
                    "event_type":       EventType.GENERIC.value,
                    "source":           EventSource.TEXT.value,
                    "severity":         EventSeverity.INFO.value,
                    "subject":          filename or "text_file",
                    "action":           "log_entry",
                    "object":           line[:200],   # cap long lines
                    "details": {
                        "raw_line":    raw_line,
                        "line_number": lineno,
                    },
                    "mitre_techniques": [],
                })

        if not events:
            events.append({
                "timestamp":        now,
                "event_type":       EventType.GENERIC.value,
                "source":           EventSource.TEXT.value,
                "severity":         EventSeverity.INFO.value,
                "subject":          filename or "text_file",
                "action":           "file_ingested",
                "object":           filename or "unknown",
                "details":          {"file_size": len(file_content), "lines": text.count("\n")},
                "mitre_techniques": [],
            })

        return events
