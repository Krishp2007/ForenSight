import io
import os
import tempfile

# Fix scapy cache permission issues on Windows before import
os.environ.setdefault(
    'SCAPY_CACHE_DIR',
    os.path.join(tempfile.gettempdir(), 'scapy_cache_forensight')
)
os.makedirs(os.environ['SCAPY_CACHE_DIR'], exist_ok=True)

from datetime import datetime
import logging
from typing import List, Dict, Any, Optional

from scapy.utils import PcapReader
from scapy.layers.inet import IP, TCP, UDP
from backend.app.parsers.base import BaseParser
from backend.app.schemas.event import EventSource, EventType, EventSeverity
from backend.app.knowledge.mitre_mapper import MitreMapper

logger = logging.getLogger(__name__)

class PcapParser(BaseParser):
    def parse(self, file_content: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        events = []
        
        try:
            # 1. Feed Scapy PcapReader with an in-memory BytesIO stream
            pcap_stream = io.BytesIO(file_content)
            
            # Limit the number of packets we parse per file to prevent memory exhaustion
            packet_limit = 2000
            packet_count = 0
            
            with PcapReader(pcap_stream) as packets:
                for packet in packets:
                    packet_count += 1
                    if packet_count > packet_limit:
                        logger.info(f"PCAP packet parsing limit ({packet_limit}) reached. Stopping.")
                        break
                        
                    event_dict = self._parse_packet(packet)
                    if event_dict:
                        events.append(event_dict)
                        
        except Exception as e:
            logger.warning(f"Could not parse file as binary PCAP network capture ({e}). Attempting mock fallback.")
            # Fallback event
            fallback_time = datetime.utcnow()
            events.append({
                "timestamp": fallback_time,
                "event_type": EventType.NETWORK_CONNECTION.value,
                "source": EventSource.PCAP.value,
                "severity": EventSeverity.INFO.value,
                "subject": "NetworkInterface",
                "action": "packet_capture_fallback",
                "object": filename or "unknown_pcap_file",
                "details": {
                    "raw_fallback": True,
                    "file_size": len(file_content)
                },
                "mitre_techniques": []
            })
            
        return events

    def _parse_packet(self, packet) -> Optional[Dict[str, Any]]:
        """Extract network parameters from Scapy packet and normalize to CFM."""
        try:
            # Check for IP layer
            if not packet.haslayer(IP):
                return None
                
            ip_layer = packet[IP]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
            proto = ip_layer.proto
            
            # Extract timestamp from packet metadata (defaults to current time if unavailable)
            pkt_time = float(packet.time) if hasattr(packet, 'time') and packet.time else datetime.utcnow().timestamp()
            timestamp = datetime.utcfromtimestamp(pkt_time)
            
            sport, dport = None, None
            proto_name = "IP"
            details = {
                "length": len(packet),
                "ttl": ip_layer.ttl,
                "proto_code": proto
            }
            
            # Resolve TCP/UDP layer details
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                sport = tcp_layer.sport
                dport = tcp_layer.dport
                proto_name = "TCP"
                details.update({
                    "sport": sport,
                    "dport": dport,
                    "flags": str(tcp_layer.flags),
                    "seq": tcp_layer.seq
                })
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                sport = udp_layer.sport
                dport = udp_layer.dport
                proto_name = "UDP"
                details.update({
                    "sport": sport,
                    "dport": dport
                })
                
            # Define Subject-Action-Object triple
            subj = src_ip
            act = f"sent_{proto_name.lower()}_packet"
            obj = f"{dst_ip}:{dport}" if dport else dst_ip
            
            severity = EventSeverity.INFO.value
            techniques = []
            
            # Identify suspicious network ports (e.g. Metasploit, suspected C2 beacons)
            if dport in (4444, 1337, 6667, 8080):
                severity = EventSeverity.MEDIUM.value
                techniques = MitreMapper.tag_from_text(str(dport))
            elif dport == 22 and src_ip.startswith("10."):
                severity = EventSeverity.LOW.value
                
            return {
                "timestamp": timestamp,
                "event_type": EventType.NETWORK_CONNECTION.value,
                "source": EventSource.PCAP.value,
                "severity": severity,
                "subject": subj,
                "action": act,
                "object": obj,
                "details": details,
                "mitre_techniques": techniques
            }
        except Exception:
            return None
