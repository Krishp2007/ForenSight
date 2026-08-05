"""
Entity & Relationship Extraction Layer — ForenSight
=====================================================
Deterministic entity and relationship extractor that operates over normalized
forensic events to identify Host, User, Process, File, IPAddress, Domain, Port,
RegistryKey, Service, and Hash entities along with provenanced relationships.
"""

import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

IP_V4_PATTERN = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
MD5_PATTERN = re.compile(r"\b[a-fA-F0-9]{32}\b")
SHA256_PATTERN = re.compile(r"\b[a-fA-F0-9]{64}\b")


class EntityRelationshipExtractor:

    @staticmethod
    def _is_private_ip(ip: str) -> bool:
        clean = ip.split(":")[0].strip()
        parts = clean.split(".")
        if len(parts) != 4:
            return False
        try:
            p0, p1 = int(parts[0]), int(parts[1])
            if p0 in (10, 127) or (p0 == 172 and 16 <= p1 <= 31) or (p0 == 192 and p1 == 168):
                return True
        except ValueError:
            pass
        return False

    @classmethod
    def extract_from_event(cls, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inspect normalized forensic event and extract entities, relationships,
        confidence scores, and evidence provenance.
        """
        entities: List[Dict[str, Any]] = []
        relationships: List[Dict[str, Any]] = []

        host = event.get("host", {}) or {}
        user = event.get("user", {}) or {}
        proc = event.get("process", {}) or {}
        pproc = event.get("parent_process", {}) or {}
        file_obj = event.get("file", {}) or {}
        net = event.get("network", {}) or {}
        reg = event.get("registry", {}) or {}
        svc = event.get("service", {}) or {}
        auth = event.get("authentication", {}) or {}

        cid = str(event.get("case_id", ""))
        ev_id = str(event.get("evidence_id", ""))
        event_id = str(event.get("event_id", event.get("_id", "")))
        ts = event.get("timestamp")
        ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts or "")
        src_file = event.get("source_file", "")

        prov = {
            "case_id": cid,
            "evidence_id": ev_id,
            "event_id": event_id,
            "source_file": src_file,
            "timestamp": ts_str,
            "relationship_type": "observed",
        }

        # 1. Host Entity
        host_name = host.get("hostname")
        if host_name:
            entities.append({
                "type": "Host",
                "value": host_name,
                "confidence": 1.0,
                "extraction_method": "normalized_field",
            })
            relationships.append({
                "source_type": "Event",
                "source": event_id,
                "rel_type": "OCCURRED_ON",
                "target_type": "Host",
                "target": host_name,
                **prov,
            })

        # 2. User Entity
        username = user.get("username")
        if username:
            user_val = f"{user.get('domain')}\\{username}" if user.get("domain") else username
            entities.append({
                "type": "User",
                "value": user_val,
                "username": username,
                "domain": user.get("domain"),
                "confidence": 1.0,
                "extraction_method": "normalized_field",
            })

        # 3. Process Entity
        proc_name = proc.get("name")
        pid = proc.get("pid")
        if proc_name:
            proc_val = f"{host_name or 'host'}:{pid or 0}:{proc_name}"
            entities.append({
                "type": "Process",
                "value": proc_val,
                "name": proc_name,
                "pid": pid,
                "path": proc.get("path"),
                "command_line": proc.get("command_line"),
                "hash": proc.get("hash"),
                "confidence": 1.0,
                "extraction_method": "normalized_field",
            })

            if username:
                user_val = f"{user.get('domain')}\\{username}" if user.get("domain") else username
                relationships.append({
                    "source_type": "User",
                    "source": user_val,
                    "rel_type": "EXECUTED",
                    "target_type": "Process",
                    "target": proc_val,
                    **prov,
                })

        # 4. Parent Process & SPAWNED Relationship
        pproc_name = pproc.get("name")
        if pproc_name and proc_name:
            pproc_val = f"{host_name or 'host'}:{pproc.get('pid') or 0}:{pproc_name}"
            entities.append({
                "type": "Process",
                "value": pproc_val,
                "name": pproc_name,
                "pid": pproc.get("pid"),
                "confidence": 0.9,
                "extraction_method": "parent_process_field",
            })
            relationships.append({
                "source_type": "Process",
                "source": pproc_val,
                "rel_type": "SPAWNED",
                "target_type": "Process",
                "target": f"{host_name or 'host'}:{pid or 0}:{proc_name}",
                **prov,
            })

        # 5. Network (IPAddress & Port & Domain)
        dst_ip = net.get("destination_ip") or auth.get("source_ip")
        dst_port = net.get("destination_port")
        if dst_ip:
            is_priv = cls._is_private_ip(dst_ip)
            entities.append({
                "type": "IPAddress",
                "value": dst_ip,
                "is_private": is_priv,
                "confidence": 1.0,
                "extraction_method": "network_field",
            })

            if proc_name:
                proc_val = f"{host_name or 'host'}:{pid or 0}:{proc_name}"
                relationships.append({
                    "source_type": "Process",
                    "source": proc_val,
                    "rel_type": "CONNECTED_TO",
                    "target_type": "IPAddress",
                    "target": dst_ip,
                    **prov,
                })

            if dst_port:
                port_val = f"{dst_port}:TCP"
                entities.append({
                    "type": "Port",
                    "value": port_val,
                    "port_number": dst_port,
                    "protocol": net.get("protocol") or "TCP",
                    "confidence": 1.0,
                    "extraction_method": "network_field",
                })
                relationships.append({
                    "source_type": "IPAddress",
                    "source": dst_ip,
                    "rel_type": "USES_PORT",
                    "target_type": "Port",
                    "target": port_val,
                    **prov,
                })

        domain_name = net.get("domain") or net.get("dns_query")
        if domain_name:
            entities.append({
                "type": "Domain",
                "value": domain_name,
                "confidence": 1.0,
                "extraction_method": "dns_field",
            })
            if proc_name:
                proc_val = f"{host_name or 'host'}:{pid or 0}:{proc_name}"
                relationships.append({
                    "source_type": "Process",
                    "source": proc_val,
                    "rel_type": "RESOLVED",
                    "target_type": "Domain",
                    "target": domain_name,
                    **prov,
                })
            if dst_ip:
                relationships.append({
                    "source_type": "Domain",
                    "source": domain_name,
                    "rel_type": "RESOLVES_TO",
                    "target_type": "IPAddress",
                    "target": dst_ip,
                    **prov,
                })

        # 6. File Entity & Activity
        file_path = file_obj.get("path") or file_obj.get("name")
        if file_path:
            entities.append({
                "type": "File",
                "value": file_path,
                "name": file_obj.get("name"),
                "path": file_path,
                "sha256": file_obj.get("sha256"),
                "confidence": 1.0,
                "extraction_method": "file_field",
            })
            if proc_name:
                proc_val = f"{host_name or 'host'}:{pid or 0}:{proc_name}"
                action_lower = str(event.get("action", "")).lower()
                rel_type = "MODIFIED"
                if "create" in action_lower or "write" in action_lower:
                    rel_type = "CREATED"
                elif "delete" in action_lower or "remove" in action_lower:
                    rel_type = "DELETED"

                relationships.append({
                    "source_type": "Process",
                    "source": proc_val,
                    "rel_type": rel_type,
                    "target_type": "File",
                    "target": file_path,
                    **prov,
                })

        # 7. Registry Entity
        reg_key = reg.get("key")
        if reg_key:
            entities.append({
                "type": "RegistryKey",
                "value": reg_key,
                "confidence": 1.0,
                "extraction_method": "registry_field",
            })
            if proc_name:
                proc_val = f"{host_name or 'host'}:{pid or 0}:{proc_name}"
                relationships.append({
                    "source_type": "Process",
                    "source": proc_val,
                    "rel_type": "MODIFIED_REGISTRY",
                    "target_type": "RegistryKey",
                    "target": reg_key,
                    **prov,
                })

        # 8. Service Entity
        svc_name = svc.get("name")
        if svc_name:
            svc_val = f"{host_name or 'host'}:{svc_name}"
            entities.append({
                "type": "Service",
                "value": svc_val,
                "name": svc_name,
                "binary_path": svc.get("binary_path"),
                "confidence": 1.0,
                "extraction_method": "service_field",
            })
            if proc_name:
                proc_val = f"{host_name or 'host'}:{pid or 0}:{proc_name}"
                relationships.append({
                    "source_type": "Process",
                    "source": proc_val,
                    "rel_type": "CREATED_SERVICE",
                    "target_type": "Service",
                    "target": svc_val,
                    **prov,
                })

        return {
            "entities": entities,
            "relationships": relationships,
        }
