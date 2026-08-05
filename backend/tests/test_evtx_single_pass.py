import pytest
from backend.app.parsers.evtx_parser import EvtxParser

def test_evtx_parser_instantiation():
    parser = EvtxParser()
    assert parser is not None
    # Verify empty content returns empty list or fallback gracefully
    res = parser.parse(b"", filename="empty.evtx")
    assert isinstance(res, list)
