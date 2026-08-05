import io
import os
import tempfile
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional

os.environ.setdefault(
    'SCAPY_CACHE_DIR',
    os.path.join(tempfile.gettempdir(), 'scapy_cache_forensight')
)
os.makedirs(os.environ['SCAPY_CACHE_DIR'], exist_ok=True)

from scapy.utils import PcapReader
from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.dns import DNS, DNSQR
from scapy.layers.http import HTTPRequest

from backend.app.parsers.base import BaseParser
from backend.app.parsers.extractor import EntityRelationshipExtractor
from backend.app.schemas.event import EventSource, EventType, EventSeverity
from backend.app.knowledge.mitre_mapper import MitreMapper

logger = logging.getLogger(__name__)


class PcapParser(BaseParser):
    def parse(self, file_content: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        events = []
        try:
            pcap_stream = io.BytesIO(file_content)
            packet_limit = 2000
            packet_count = 0

            with PcapReader(pcap_stream) as packets:
                for packet in packets:
                    packet_count += 1
                    if packet_count > packet_limit:
                        break

                    event_dict = self._parse_packet(packet, filename=filename)
                    if event_dict:
                        events.append(event_dict)

        except Exception as e:
            logger.warning(f"Could not parse binary PCAP ({e}). Using fallback.")
            events.append({
                "timestamp": datetime.utcnow(),
                "event_type": EventType.NETWORK_CONNECTION.value,
                "source": EventSource.PCAP.value,
                "severity": EventSeverity.INFO.value,
                "subject": "NetworkInterface",
                "action": "packet_capture_fallback",
                "object": filename or "unknown_pcap_file",
                "details": {"raw_fallback": True, "file_size": len(file_content)},
                "mitre_techniques": [],
            })

        return events

    def _parse_packet(self, packet, filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            if not packet.haslayer(IP):
                return None

            ip_layer = packet[IP]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
            proto = ip_layer.proto

            pkt_time = float(packet.time) if hasattr(packet, 'time') and packet.time else datetime.utcnow().timestamp()
            timestamp = datetime.utcfromtimestamp(pkt_time)

            sport, dport = None, None
            proto_name = "IP"
            details = {
                "length": len(packet),
                "ttl": ip_layer.ttl,
                "proto_code": proto,
            }

            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                sport = tcp_layer.sport
                dport = tcp_layer.dport
                proto_name = "TCP"
                details.update({"sport": sport, "dport": dport, "flags": str(tcp_layer.flags)})
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                sport = udp_layer.sport
                dport = udp_layer.dport
                proto_name = "UDP"
                details.update({"sport": sport, "dport": dport})

            # Check for Layer 7 protocols (DNS, HTTP)
            dns_query, domain_name, http_url = None, None, None
            if packet.haslayer(DNS) and packet.haslayer(DNSQR):
                qr = packet[DNSQR]
                dns_query = qr.qname.decode('utf-8', errors='ignore').rstrip('.') if hasattr(qr.qname, 'decode') else str(qr.qname).rstrip('.')
                domain_name = dns_query
                details["dns_query"] = dns_query

            if packet.haslayer(HTTPRequest):
                http = packet[HTTPRequest]
                host = http.Host.decode('utf-8', errors='ignore') if hasattr(http, 'Host') and http.Host else dst_ip
                path = http.Path.decode('utf-8', errors='ignore') if hasattr(http, 'Path') and http.Path else "/"
                http_url = f"http://{host}{path}"
                domain_name = host
                details["http_url"] = http_url

            net_obj = {
                "source_ip": src_ip,
                "source_port": sport,
                "destination_ip": dst_ip,
                "destination_port": dport,
                "protocol": proto_name,
                "domain": domain_name,
                "dns_query": dns_query,
                "url": http_url,
                "direction": "outbound" if EntityRelationshipExtractor._is_private_ip(src_ip) else "inbound",
            }

            severity = EventSeverity.INFO.value
            techniques: List[str] = []
            if dport in (4444, 1337, 6667, 8080):
                severity = EventSeverity.MEDIUM.value
                techniques = MitreMapper.tag_from_text(str(dport))

            act = f"sent_{proto_name.lower()}_packet"
            obj = f"{dst_ip}:{dport}" if dport else dst_ip

            base_event = {
                "source_file": filename or "pcap_file",
                "source_type": EventSource.PCAP.value,
                "timestamp": timestamp,
                "event_type": EventType.NETWORK_CONNECTION.value,
                "event_category": "network_packet",
                "severity": severity,

                "host": {"hostname": "NetworkHost", "ip": src_ip, "os": None},
                "user": {"username": None, "domain": None, "sid": None},
                "process": {"pid": None, "ppid": None, "name": None, "path": None, "command_line": None, "hash": None},
                "parent_process": {"pid": None, "name": None, "path": None, "command_line": None},
                "file": {"name": None, "path": None, "extension": None, "size": None, "md5": None, "sha1": None, "sha256": None},
                "network": net_obj,
                "registry": {"key": None, "value_name": None, "value_data": None, "operation": None},
                "service": {"name": None, "display_name": None, "binary_path": None, "start_type": None},
                "authentication": {"logon_type": None, "source_ip": src_ip, "status": None, "failure_reason": None},

                "subject": src_ip,
                "action": act,
                "object": obj,
                "details": details,
                "raw_event": {"len": len(packet), "proto": proto_name},
                "mitre_techniques": techniques,
                "parser_metadata": {
                    "confidence": 1.0,
                    "extraction_method": "scapy_pcap_reader",
                },
            }

            extracted = EntityRelationshipExtractor.extract_from_event(base_event)
            base_event["entities"] = extracted["entities"]
            base_event["relationships"] = extracted["relationships"]

            return base_event
        except Exception:
            return None
