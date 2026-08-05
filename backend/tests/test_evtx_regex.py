import pytest
from backend.app.parsers.evtx_parser import _parse_xml_record_fast

def test_parse_xml_record_fast_with_attributes_and_newlines():
    xml = """
    <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
      <System>
        <Provider Name="Microsoft-Windows-Security-Auditing" Guid="{5484fe3a-3250-4632-8025-0d3c0b40a324}" />
        <EventID Qualifiers="16384">
            4688
        </EventID>
        <TimeCreated SystemTime="2026-08-04T19:32:11.123456Z" />
        <Computer> DESKTOP-01 </Computer>
      </System>
      <EventData>
        <Data Name="NewProcessName">C:\\Windows\\System32\\cmd.exe</Data>
        <Data Name="CommandLine">cmd.exe /c whoami</Data>
      </EventData>
    </Event>
    """
    res = _parse_xml_record_fast(xml, filename="test.evtx")
    assert res is not None
    assert res["details"]["EventID"] == 4688
    assert res["details"]["Provider"] == "Microsoft-Windows-Security-Auditing"
    assert res["details"]["Computer"] == "DESKTOP-01"
    assert res["details"]["NewProcessName"] == "C:\\Windows\\System32\\cmd.exe"
