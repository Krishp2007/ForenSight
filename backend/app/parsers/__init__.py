from .base import BaseParser
from .evtx_parser import EvtxParser
from .browser_parser import BrowserParser
from .csv_parser import CsvParser
from .json_parser import JsonParser
from .text_parser import TextParser

# PcapParser is imported lazily to avoid scapy loading on every import

def get_parser(file_type: str) -> BaseParser:
    """Retrieve corresponding parser instance based on file type."""
    ft = file_type.lower()

    if ft == "evtx":
        return EvtxParser()
    elif ft in ("pcap", "pcapng"):
        import os, tempfile
        os.environ.setdefault(
            'SCAPY_CACHE_DIR',
            os.path.join(tempfile.gettempdir(), 'scapy_cache_forensight')
        )
        os.makedirs(os.environ['SCAPY_CACHE_DIR'], exist_ok=True)
        from .pcap_parser import PcapParser
        return PcapParser()
    elif ft in ("browser_sqlite", "browser"):
        return BrowserParser()
    elif ft == "csv":
        return CsvParser()
    elif ft == "text":
        return TextParser()
    else:
        return JsonParser()
