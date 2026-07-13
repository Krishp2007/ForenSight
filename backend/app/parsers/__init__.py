from .base import BaseParser
from .evtx_parser import EvtxParser
from .browser_parser import BrowserParser
from .pcap_parser import PcapParser
from .csv_parser import CsvParser
from .json_parser import JsonParser

# Factory mapping to retrieve parser class by name/extension
PARSERS = {
    "evtx": EvtxParser,
    "browser": BrowserParser,
    "pcap": PcapParser,
    "csv": CsvParser,
    "json": JsonParser
}

def get_parser(file_type: str) -> BaseParser:
    """Retrieve corresponding parser instance based on file type."""
    parser_cls = PARSERS.get(file_type.lower(), JsonParser)
    return parser_cls()
