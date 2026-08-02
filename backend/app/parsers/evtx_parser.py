import tempfile
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from functools import lru_cache
import logging
from typing import List, Dict, Any, Optional

import Evtx.Evtx as evtx
from backend.app.parsers.base import BaseParser
from backend.app.schemas.event import EventSource, EventType, EventSeverity
from backend.app.knowledge.mitre_mapper import MitreMapper

logger = logging.getLogger(__name__)

NS_PREFIX = '{http://schemas.microsoft.com/win/2004/08/events/event}'

# Pre-build tag strings once — avoids repeated string concatenation per record
_SYS       = f'{NS_PREFIX}System'
_EVTDATA   = f'{NS_PREFIX}EventData'
_EVTID     = f'{NS_PREFIX}EventID'
_PROVIDER  = f'{NS_PREFIX}Provider'
_TIMECREATED = f'{NS_PREFIX}TimeCreated'
_DATA      = f'{NS_PREFIX}Data'


def _fast_parse_ts(time_str: str) -> datetime:
    """Parse SystemTime string to datetime as fast as possible."""
    try:
        # Most common: "2023-01-15T10:30:45.123456Z" → strip sub-seconds and Z
        s = time_str[:19]          # "2023-01-15T10:30:45"
        return datetime(
            int(s[0:4]), int(s[5:7]), int(s[8:10]),
            int(s[11:13]), int(s[14:16]), int(s[17:19])
        )
    except Exception:
        return datetime.utcnow()


# Cache MitreMapper event_id lookups — same event_id will be looked up thousands of times
@lru_cache(maxsize=256)
def _mitre_for_event_id(event_id: int) -> list:
    return MitreMapper.tag_from_event_id(event_id)


class EvtxParser(BaseParser):
    def parse(self, file_content: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parse EVTX bytes synchronously — called from a thread executor by the pipeline."""
        events = []
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".evtx") as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name

            with evtx.Evtx(tmp_path) as log:
                for record in log.records():
                    try:
                        xml_str = record.xml()
                        event_dict = self._parse_xml_record(xml_str)
                        if event_dict:
                            events.append(event_dict)
                    except Exception as re:
                        logger.debug(f"Skipping corrupt EVTX record: {re}")

        except Exception as e:
            logger.warning(f"Could not parse EVTX ({e}). Using fallback.")
            events.append({
                "timestamp": datetime.utcnow(),
                "event_type": EventType.GENERIC.value,
                "source": EventSource.EVTX.value,
                "severity": EventSeverity.INFO.value,
                "subject": "System",
                "action": "parsed_fallback",
                "object": filename or "unknown_file",
                "details": {"raw_fallback": True, "file_size": len(file_content)},
                "mitre_techniques": [],
            })
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

        return events

    def _parse_xml_record(self, xml_str: str) -> Optional[Dict[str, Any]]:
        try:
            root = ET.fromstring(xml_str)

            # Try namespaced first, then bare (no-namespace fallback files)
            system = root.find(_SYS) or root.find('System')
            if system is None:
                return None

            # Event ID
            eid_elem = system.find(_EVTID) or system.find('EventID')
            event_id = int(eid_elem.text) if eid_elem is not None and eid_elem.text else 0

            # Provider
            prov_elem = system.find(_PROVIDER) or system.find('Provider')
            provider  = prov_elem.get('Name', 'Unknown') if prov_elem is not None else 'Unknown'

            # Timestamp — fast integer slice parser
            tc_elem  = system.find(_TIMECREATED) or system.find('TimeCreated')
            time_str = tc_elem.get('SystemTime') if tc_elem is not None else None
            timestamp = _fast_parse_ts(time_str) if time_str else datetime.utcnow()

            # EventData key-value pairs
            ev_data = root.find(_EVTDATA) or root.find('EventData')
            details: Dict[str, Any] = {"EventID": event_id, "Provider": provider}
            if ev_data is not None:
                for d in ev_data:
                    name = d.get('Name')
                    if name:
                        details[name] = d.text

            # Subject / Action / Object mapping
            subj = f"System (Event {event_id})"
            act  = "occurred"
            obj  = f"Provider {provider}"
            event_type = EventType.GENERIC.value
            severity   = EventSeverity.INFO.value
            techniques: list = []

            if event_id == 4624:
                event_type = EventType.AUTH_EVENT.value
                subj = f"{details.get('TargetDomainName','?')}\\{details.get('TargetUserName','?')}"
                act  = "logged_on_successfully"
                obj  = f"from IP {details.get('IpAddress','Local')}"
                severity = EventSeverity.LOW.value

            elif event_id == 4625:
                event_type = EventType.AUTH_EVENT.value
                subj = f"{details.get('TargetDomainName','?')}\\{details.get('TargetUserName','?')}"
                act  = "failed_logon_attempt"
                obj  = f"from IP {details.get('IpAddress','Local')}"
                severity   = EventSeverity.MEDIUM.value
                techniques = _mitre_for_event_id(4625)

            elif event_id == 4688:
                event_type = EventType.PROCESS_CREATION.value
                parent = details.get('ParentProcessName', '')
                child  = details.get('NewProcessName', '')
                cmd    = details.get('CommandLine', '')
                subj = os.path.basename(parent) if parent else 'Unknown'
                obj  = (f"{os.path.basename(child)} ({cmd})" if cmd else os.path.basename(child)) if child else 'Unknown'
                act  = "spawned"
                severity = EventSeverity.LOW.value
                if cmd:
                    cmd_l = cmd.lower()
                    if "powershell" in cmd_l and "-enc" in cmd_l:
                        severity   = EventSeverity.HIGH.value
                        techniques = MitreMapper.tag_from_text(cmd_l)
                    elif "whoami" in cmd_l or "net user" in cmd_l:
                        severity   = EventSeverity.MEDIUM.value
                        techniques = MitreMapper.tag_from_text(cmd_l)
                    else:
                        techniques = _mitre_for_event_id(4688)
                else:
                    techniques = _mitre_for_event_id(4688)

            elif event_id in (4663, 4660):
                event_type = EventType.FILE_MODIFICATION.value
                process = details.get('ProcessName', '')
                subj = os.path.basename(process) if process else 'Unknown'
                act  = "accessed" if event_id == 4663 else "deleted"
                obj  = details.get('ObjectName', 'Unknown')
                severity = EventSeverity.LOW.value

            elif event_id in (4657, 5039):
                event_type = EventType.REGISTRY_CHANGE.value
                process = details.get('ProcessName', '')
                subj = os.path.basename(process) if process else 'Unknown'
                act  = "modified_registry"
                obj  = details.get('ObjectName', 'Unknown')
                severity = EventSeverity.LOW.value

            return {
                "timestamp":       timestamp,
                "event_type":      event_type,
                "source":          EventSource.EVTX.value,
                "severity":        severity,
                "subject":         subj,
                "action":          act,
                "object":          obj,
                "details":         details,
                "mitre_techniques": techniques,
            }
        except Exception as e:
            logger.debug(f"Failed parsing EVTX record: {e}")
            return None
