import magic
import logging
from typing import Tuple
from backend.app.schemas.evidence import EvidenceType

logger = logging.getLogger(__name__)

# EVTX binary header signatures
EVTX_HEADER = b"ElfFile\x00"
# PCAP binary header signatures
PCAP_MAGIC_1 = b"\xd4\xc3\xb2\xa1"
PCAP_MAGIC_2 = b"\xa1\xb2\xc3\xd4"
PCAPNG_MAGIC = b"\x0a\x0d\x0d\x0a"
# SQLite database header
SQLITE_HEADER = b"SQLite format 3\x00"

class FileDetector:
    @staticmethod
    def detect_type(file_content: bytes, filename: str) -> EvidenceType:
        """Inspect file header bytes and MIME types to determine EvidenceType."""
        # 1. Inspect raw headers (first 100 bytes)
        header = file_content[:100]
        
        # Check EVTX header signature
        if header.startswith(EVTX_HEADER):
            logger.info(f"Detected EVTX binary header signature for {filename}")
            return EvidenceType.EVTX
            
        # Check PCAP/PCAPNG signatures
        if header.startswith(PCAP_MAGIC_1) or header.startswith(PCAP_MAGIC_2) or header.startswith(PCAPNG_MAGIC):
            logger.info(f"Detected PCAP/PCAPNG network signature for {filename}")
            return EvidenceType.PCAP
            
        # Check SQLite signature
        if header.startswith(SQLITE_HEADER):
            logger.info(f"Detected SQLite database signature for {filename}")
            return EvidenceType.BROWSER_SQLITE

        # 2. Inspect MIME type using python-magic
        try:
            mime = magic.from_buffer(file_content, mime=True)
            logger.info(f"python-magic detected MIME type: {mime} for {filename}")
            
            if "csv" in mime or "excel" in mime:
                return EvidenceType.CSV
            elif "json" in mime:
                return EvidenceType.JSON
            elif "sqlite" in mime:
                return EvidenceType.BROWSER_SQLITE
            elif "pcap" in mime:
                return EvidenceType.PCAP
        except Exception as e:
            logger.debug(f"python-magic inspection failed: {e}")

        # 3. Fallback to file extension
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        logger.info(f"Falling back to extension lookup for {filename} (ext: {ext})")
        
        if ext == "evtx":
            return EvidenceType.EVTX
        elif ext in ("pcap", "pcapng", "cap"):
            return EvidenceType.PCAP
        elif ext in ("db", "sqlite", "sqlite3"):
            return EvidenceType.BROWSER_SQLITE
        elif ext == "csv":
            return EvidenceType.CSV
        elif ext == "json":
            return EvidenceType.JSON
            
        # Default fallback
        return EvidenceType.JSON
