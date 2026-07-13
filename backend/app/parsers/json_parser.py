import json
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional

from backend.app.parsers.base import BaseParser
from backend.app.schemas.event import EventSource, EventType, EventSeverity

logger = logging.getLogger(__name__)

class JsonParser(BaseParser):
    def parse(self, file_content: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        events = []
        
        try:
            # 1. Decode byte stream as UTF-8 string
            text_data = file_content.decode('utf-8', errors='replace')
            data = json.loads(text_data)
            
            # 2. Support list of events or single event dictionary
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        event_dict = self._parse_json_item(item, filename)
                        if event_dict:
                            events.append(event_dict)
            elif isinstance(data, dict):
                event_dict = self._parse_json_item(data, filename)
                if event_dict:
                    events.append(event_dict)
            else:
                raise ValueError("JSON content is neither a list nor a dictionary.")
                
        except Exception as e:
            logger.warning(f"Could not parse file as JSON ({e}). Attempting mock fallback.")
            fallback_time = datetime.utcnow()
            events.append({
                "timestamp": fallback_time,
                "event_type": EventType.JSON.value,
                "source": EventSource.JSON.value,
                "severity": EventSeverity.INFO.value,
                "subject": "JsonParser",
                "action": "parsed_fallback",
                "object": filename or "unknown_json_file",
                "details": {
                    "raw_fallback": True,
                    "file_size": len(file_content)
                },
                "mitre_techniques": []
            })
            
        return events

    def _parse_json_item(self, item: Dict[str, Any], filename: Optional[str]) -> Optional[Dict[str, Any]]:
        """Normalize loaded JSON keys into standardized CFM attributes."""
        try:
            # 1. Resolve Timestamp
            ts_val = item.get("timestamp") or item.get("time") or item.get("datetime")
            timestamp = datetime.utcnow()
            if ts_val:
                # Try parsing formats
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S"):
                    try:
                        timestamp = datetime.strptime(str(ts_val).strip(), fmt)
                        break
                    except Exception:
                        pass
                        
            # 2. Resolve Subject-Action-Object Triples
            subj = item.get("subject") or item.get("actor") or item.get("user") or "System"
            act = item.get("action") or item.get("operation") or "occurred"
            obj = item.get("object") or item.get("target") or item.get("path") or filename or "unknown_resource"
            
            # 3. Resolve Severity
            sev_val = str(item.get("severity") or item.get("level") or "info").lower().strip()
            severity = EventSeverity.INFO.value
            if sev_val in [s.value for s in EventSeverity]:
                severity = sev_val
                
            # 4. Resolve Event Type
            type_val = str(item.get("event_type") or item.get("type") or "generic").lower().strip()
            event_type = EventType.GENERIC.value
            if type_val in [t.value for t in EventType]:
                event_type = type_val
                
            # 5. Extract Mitre Techniques
            mitre_techniques = item.get("mitre_techniques") or item.get("techniques")
            if not isinstance(mitre_techniques, list):
                mitre_techniques = []
            else:
                mitre_techniques = [str(t) for t in mitre_techniques]
                
            # Details holds all key-value parameters
            details = item.copy()
            
            return {
                "timestamp": timestamp,
                "event_type": event_type,
                "source": EventSource.JSON.value,
                "severity": severity,
                "subject": str(subj),
                "action": str(act),
                "object": str(obj),
                "details": details,
                "mitre_techniques": mitre_techniques
            }
        except Exception:
            return None
