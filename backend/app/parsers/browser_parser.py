import tempfile
import os
import sqlite3
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional

from backend.app.parsers.base import BaseParser
from backend.app.schemas.event import EventSource, EventType, EventSeverity
from backend.app.knowledge.mitre_mapper import MitreMapper

logger = logging.getLogger(__name__)

class BrowserParser(BaseParser):
    def parse(self, file_content: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        events = []
        
        # 1. Write database bytes to temporary file path
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name
            
        conn = None
        try:
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            
            # 2. Check if Chrome History (urls table exists)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='urls';")
            is_chrome = cursor.fetchone() is not None
            
            if is_chrome:
                events.extend(self._parse_chrome_history(cursor))
            else:
                # 3. Check if Firefox History (moz_places table exists)
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='moz_places';")
                is_firefox = cursor.fetchone() is not None
                if is_firefox:
                    events.extend(self._parse_firefox_history(cursor))
                else:
                    raise ValueError("No recognized Chrome or Firefox history tables found.")
                    
        except Exception as e:
            logger.warning(f"Could not parse file as browser SQLite database ({e}). Attempting mock fallback.")
            # Fallback event
            fallback_time = datetime.utcnow()
            events.append({
                "timestamp": fallback_time,
                "event_type": EventType.BROWSER_HISTORY.value,
                "source": EventSource.BROWSER.value,
                "severity": EventSeverity.INFO.value,
                "subject": "Browser",
                "action": "parsed_fallback",
                "object": filename or "unknown_history_file",
                "details": {
                    "raw_fallback": True,
                    "file_size": len(file_content)
                },
                "mitre_techniques": []
            })
        finally:
            if conn:
                conn.close()
            # Clean up temp database file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
        return events

    def _parse_chrome_history(self, cursor) -> List[Dict[str, Any]]:
        """Extract Chrome history and convert to CFM events."""
        events = []
        try:
            # Query Chrome URLs table
            # last_visit_time is represented as microseconds since Jan 1, 1601 UTC
            cursor.execute("""
                SELECT url, title, visit_count, last_visit_time 
                FROM urls 
                ORDER BY last_visit_time DESC 
                LIMIT 1000
            """)
            
            for row in cursor.fetchall():
                url, title, visit_count, raw_time = row
                
                # Convert Chrome Epoch (1601-based microseconds) to Python datetime
                try:
                    timestamp = datetime(1601, 1, 1) + timedelta(microseconds=raw_time)
                except Exception:
                    timestamp = datetime.utcnow()
                    
                severity = EventSeverity.INFO.value
                techniques = []
                
                # Highlight potentially malicious domains or downloads
                url_lower = url.lower()
                if "onion" in url_lower or "torproject" in url_lower:
                    severity = EventSeverity.HIGH.value
                    techniques = MitreMapper.tag_from_text(url_lower)
                elif any(kw in url_lower for kw in [".exe", ".zip", ".msi", ".ps1"]):
                    severity = EventSeverity.MEDIUM.value
                    techniques = MitreMapper.tag_from_text(url_lower)

                events.append({
                    "timestamp": timestamp,
                    "event_type": EventType.BROWSER_HISTORY.value,
                    "source": EventSource.BROWSER.value,
                    "severity": severity,
                    "subject": "ChromeProcess",
                    "action": "visited",
                    "object": url,
                    "details": {
                        "title": title,
                        "visit_count": visit_count,
                        "raw_chrome_time": raw_time
                    },
                    "mitre_techniques": techniques
                })
        except Exception as e:
            logger.debug(f"Failed parsing Chrome history records: {e}")
        return events

    def _parse_firefox_history(self, cursor) -> List[Dict[str, Any]]:
        """Extract Firefox history and convert to CFM events."""
        events = []
        try:
            # Query Firefox moz_places table
            # visit_date is represented as microseconds since Jan 1, 1970 UTC in moz_historyvisits
            # For simplicity, we query url, title, visit_count, and last_visit_date (if present in moz_places)
            cursor.execute("""
                SELECT url, title, visit_count, last_visit_date 
                FROM moz_places 
                WHERE last_visit_date IS NOT NULL
                ORDER BY last_visit_date DESC 
                LIMIT 1000
            """)
            
            for row in cursor.fetchall():
                url, title, visit_count, raw_time = row
                
                # Convert Unix epoch microseconds to Python datetime
                try:
                    timestamp = datetime.utcfromtimestamp(raw_time / 1000000.0)
                except Exception:
                    timestamp = datetime.utcnow()
                    
                severity = EventSeverity.INFO.value
                techniques = []
                
                url_lower = url.lower()
                if "onion" in url_lower or "torproject" in url_lower:
                    severity = EventSeverity.HIGH.value
                    techniques = MitreMapper.tag_from_text(url_lower)
                elif any(kw in url_lower for kw in [".exe", ".zip", ".msi", ".ps1"]):
                    severity = EventSeverity.MEDIUM.value
                    techniques = MitreMapper.tag_from_text(url_lower)

                events.append({
                    "timestamp": timestamp,
                    "event_type": EventType.BROWSER_HISTORY.value,
                    "source": EventSource.BROWSER.value,
                    "severity": severity,
                    "subject": "FirefoxProcess",
                    "action": "visited",
                    "object": url,
                    "details": {
                        "title": title,
                        "visit_count": visit_count,
                        "raw_firefox_time": raw_time
                    },
                    "mitre_techniques": techniques
                })
        except Exception as e:
            logger.debug(f"Failed parsing Firefox history records: {e}")
        return events
