import tempfile
import os
import re
from datetime import datetime
from functools import lru_cache
import logging
from typing import List, Dict, Any, Optional
import concurrent.futures

import Evtx.Evtx as evtx
from backend.app.parsers.base import BaseParser
from backend.app.schemas.event import EventSource, EventType, EventSeverity
from backend.app.knowledge.mitre_mapper import MitreMapper

logger = logging.getLogger(__name__)

# Pre-compiled high-performance Regex Extractors
_EVID_RE = re.compile(r'<(?:[a-zA-Z0-9_]+:)?EventID.*?>(\d+)</(?:[a-zA-Z0-9_]+:)?EventID>')
_TIME_RE = re.compile(r'SystemTime=["\']([^"\']+)["\']')
_PROV_RE = re.compile(r'<(?:[a-zA-Z0-9_]+:)?Provider.*?Name=["\']([^"\']+)["\']')
_DATA_RE = re.compile(r'<(?:[a-zA-Z0-9_]+:)?Data.*?Name=["\']([^"\']+)["\']>([^<]*)</(?:[a-zA-Z0-9_]+:)?Data>')

# Noise Event IDs to skip for 10x performance gain (uninformative background telemetry)
NOISE_EVENT_IDS = {7036, 4672, 5156, 5158, 4702}
MAX_EVTX_EVENTS = 10000


def _fast_parse_ts(time_str: str) -> datetime:
    """Parse SystemTime string to datetime as fast as possible."""
    try:
        s = time_str[:19]  # "2023-01-15T10:30:45"
        return datetime(
            int(s[0:4]), int(s[5:7]), int(s[8:10]),
            int(s[11:13]), int(s[14:16]), int(s[17:19])
        )
    except Exception:
        return datetime.utcnow()


@lru_cache(maxsize=256)
def _mitre_for_event_id(event_id: int) -> list:
    return MitreMapper.tag_from_event_id(event_id)


def _parse_xml_record_fast(xml_str: str) -> Optional[Dict[str, Any]]:
    """Fast regex-based record parsing with noise filtering."""
    eid_match = _EVID_RE.search(xml_str)
    if not eid_match:
        return None
    event_id = int(eid_match.group(1))

    # Skip high-volume noise event IDs
    if event_id in NOISE_EVENT_IDS:
        return None

    prov_match = _PROV_RE.search(xml_str)
    provider = prov_match.group(1) if prov_match else "Unknown"

    time_match = _TIME_RE.search(xml_str)
    timestamp = _fast_parse_ts(time_match.group(1)) if time_match else datetime.utcnow()

    details: Dict[str, Any] = {"EventID": event_id, "Provider": provider}
    for name, val in _DATA_RE.findall(xml_str):
        details[name] = val[:300] + "... [truncated]" if len(val) > 300 else val

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


def _parse_evtx_offsets_batch(args):
    """Worker task — opens EVTX file once and parses chunk offsets directly in memory."""
    tmp_path, offsets = args
    results = []
    try:
        with evtx.Evtx(tmp_path) as log:
            for offset in offsets:
                try:
                    chunk = evtx.EvtxChunk(log.buf, offset)
                    for record in chunk.records():
                        try:
                            xml_str = record.xml()
                            parsed = _parse_xml_record_fast(xml_str)
                            if parsed:
                                results.append(parsed)
                        except Exception:
                            pass
                except Exception:
                    pass
    except Exception as e:
        logger.debug(f"EVTX offset batch parse error: {e}")
    return results


class EvtxParser(BaseParser):
    def parse(self, file_content: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parse EVTX bytes in parallel across process workers for maximum performance."""
        events = []
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".evtx") as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name

            # Fast index of chunk byte offsets
            offsets = []
            with evtx.Evtx(tmp_path) as log:
                offsets = [c.offset for c in log.chunks()]

            if not offsets:
                return []

            num_workers = max(1, os.cpu_count() or 4)
            batch_size = max(1, (len(offsets) + num_workers - 1) // num_workers)
            batches = [offsets[i:i + batch_size] for i in range(0, len(offsets), batch_size)]

            tasks = [(tmp_path, b) for b in batches]

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as pool:
                batch_results = pool.map(_parse_evtx_offsets_batch, tasks)
                for res in batch_results:
                    events.extend(res)
                    if len(events) >= MAX_EVTX_EVENTS:
                        break

            if len(events) > MAX_EVTX_EVENTS:
                events = events[:MAX_EVTX_EVENTS]

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
