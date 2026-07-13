import io
import csv
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional

from backend.app.parsers.base import BaseParser
from backend.app.schemas.event import EventSource, EventType, EventSeverity

logger = logging.getLogger(__name__)

class CsvParser(BaseParser):
    def parse(self, file_content: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        events = []
        
        try:
            # 1. Decode byte stream as UTF-8 string
            text_data = file_content.decode('utf-8', errors='replace')
            csv_file = io.StringIO(text_data)
            
            # 2. Sniff dialect or read header row
            reader = csv.DictReader(csv_file)
            headers = reader.fieldnames or []
            
            # Lowercase headers for flexible alignment checks
            headers_lower = [h.lower() for h in headers]
            
            # Find closest matching indices/columns
            col_map = self._detect_columns(headers_lower, headers)
            
            for row in reader:
                event_dict = self._parse_row(row, col_map, filename)
                if event_dict:
                    events.append(event_dict)
                    
        except Exception as e:
            logger.warning(f"Could not parse file as CSV ({e}). Attempting mock fallback.")
            fallback_time = datetime.utcnow()
            events.append({
                "timestamp": fallback_time,
                "event_type": EventType.CSV.value,
                "source": EventSource.CSV.value,
                "severity": EventSeverity.INFO.value,
                "subject": "CsvParser",
                "action": "parsed_fallback",
                "object": filename or "unknown_csv_file",
                "details": {
                    "raw_fallback": True,
                    "file_size": len(file_content)
                },
                "mitre_techniques": []
            })
            
        return events

    def _detect_columns(self, headers_lower: List[str], original_headers: List[str]) -> Dict[str, str]:
        """Map CSV column names to standardized EventBase properties."""
        mapping = {}
        
        # Helper to find column matching any keyword list
        def find_match(keywords: List[str]) -> Optional[str]:
            for kw in keywords:
                if kw in headers_lower:
                    idx = headers_lower.index(kw)
                    return original_headers[idx]
            return None

        mapping["timestamp"] = find_match(["timestamp", "time", "datetime", "date", "created"])
        mapping["event_type"] = find_match(["event_type", "type", "category", "event"])
        mapping["subject"] = find_match(["subject", "actor", "user", "source_name"])
        mapping["action"] = find_match(["action", "operation", "event_id"])
        mapping["object"] = find_match(["object", "target", "path", "destination"])
        mapping["severity"] = find_match(["severity", "level", "priority"])
        
        return mapping

    def _parse_row(self, row: Dict[str, str], col_map: Dict[str, str], filename: Optional[str]) -> Optional[Dict[str, Any]]:
        """Map raw CSV row attributes to a CFM event dictionary."""
        try:
            # 1. Resolve Timestamp
            ts_val = row.get(col_map.get("timestamp")) if col_map.get("timestamp") else None
            timestamp = datetime.utcnow()
            if ts_val:
                # Try parsing standard formats
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S"):
                    try:
                        timestamp = datetime.strptime(ts_val.strip(), fmt)
                        break
                    except Exception:
                        pass
                        
            # 2. Resolve Subject, Action, Object Triples (fall back to column indexes if name match fails)
            subj = row.get(col_map.get("subject")) if col_map.get("subject") else None
            if not subj:
                # Fallback: use first column value or default
                first_key = list(row.keys())[0] if row else None
                subj = row.get(first_key, "UnknownSubject") if first_key else "UnknownSubject"
                
            act = row.get(col_map.get("action")) if col_map.get("action") else "occurred"
            
            obj = row.get(col_map.get("object")) if col_map.get("object") else None
            if not obj:
                # Fallback: use second column value or default
                keys = list(row.keys())
                second_key = keys[1] if len(keys) > 1 else None
                obj = row.get(second_key, filename or "unknown_resource") if second_key else (filename or "unknown_resource")

            # 3. Resolve Severity
            sev_val = row.get(col_map.get("severity"), "info") if col_map.get("severity") else "info"
            severity = EventSeverity.INFO.value
            if sev_val:
                sev_val_clean = sev_val.strip().lower()
                if sev_val_clean in [s.value for s in EventSeverity]:
                    severity = sev_val_clean
                    
            # 4. Resolve Event Type
            type_val = row.get(col_map.get("event_type"), EventType.GENERIC.value) if col_map.get("event_type") else EventType.GENERIC.value
            event_type = EventType.GENERIC.value
            if type_val:
                type_val_clean = type_val.strip().lower()
                if type_val_clean in [t.value for t in EventType]:
                    event_type = type_val_clean
                    
            # Details holds all key-values from raw CSV row
            details = dict(row)
            
            return {
                "timestamp": timestamp,
                "event_type": event_type,
                "source": EventSource.CSV.value,
                "severity": severity,
                "subject": str(subj),
                "action": str(act),
                "object": str(obj),
                "details": details,
                "mitre_techniques": []
            }
        except Exception:
            return None
