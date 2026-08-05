from .base import BaseParser
from .browser_parser import BrowserParser
from .csv_parser import CsvParser
from .json_parser import JsonParser
from .text_parser import TextParser
from .hash_parser import HashParser

# PcapParser is imported lazily to avoid scapy loading on every import

def get_parser(file_type: str) -> BaseParser:
    """Retrieve corresponding parser instance based on file type."""
    ft = file_type.lower().lstrip(".")

    if ft in ("pcap", "pcapng"):
        import os, tempfile
        os.environ.setdefault(
            'SCAPY_CACHE_DIR',
            os.path.join(tempfile.gettempdir(), 'scapy_cache_forensight')
        )
        os.makedirs(os.environ['SCAPY_CACHE_DIR'], exist_ok=True)
        from .pcap_parser import PcapParser
        return PcapParser()
    elif ft in ("browser_sqlite", "browser", "sqlite"):
        return BrowserParser()
    elif ft == "csv":
        return CsvParser()
    elif ft in ("md5", "sha1", "sha256", "hash"):
        return HashParser()
    elif ft in ("text", "log", "txt"):
        return TextParser()
    else:
        return JsonParser()


