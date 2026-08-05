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

# Batch size for cursor.fetchmany() — keeps memory flat on large DBs
_FETCH_CHUNK = 500


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

            # 2. Check if Chrome History (visits + urls tables exist)
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
        """Extract Chrome history — one forensic event per visits row joined to urls.

        The visits table is the authoritative record of every page-load event;
        the urls table provides the URL string and page title.  Joining them
        means that a URL visited 10 times produces 10 separate forensic events,
        each with its own precise visit_time — exactly matching the semantics of
        'one browser-visits row = one forensic event'.

        Results are streamed in chunks of _FETCH_CHUNK rows so memory usage
        stays flat regardless of how many visits exist (e.g. 8,945+ rows).
        No LIMIT is applied — all valid visit records are processed.
        """
        events = []
        try:
            # Check whether the visits table exists (older Chrome builds may omit it)
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='visits';"
            )
            has_visits = cursor.fetchone() is not None

            if has_visits:
                # --- Primary path: visits JOIN urls (one row per individual visit) ---
                # visit_time is microseconds since Chrome epoch (1601-01-01 UTC)
                cursor.execute("""
                    SELECT
                        u.url,
                        u.title,
                        u.visit_count,
                        v.visit_time
                    FROM visits v
                    INNER JOIN urls u ON u.id = v.url
                    ORDER BY v.visit_time DESC
                """)
            else:
                # --- Fallback path: urls-only (one row per unique URL, no LIMIT) ---
                # last_visit_time is microseconds since Chrome epoch (1601-01-01 UTC)
                logger.debug("visits table not found — falling back to urls-only query.")
                cursor.execute("""
                    SELECT url, title, visit_count, last_visit_time
                    FROM urls
                    ORDER BY last_visit_time DESC
                """)

            # Stream results in fixed-size chunks to keep memory flat
            while True:
                rows = cursor.fetchmany(_FETCH_CHUNK)
                if not rows:
                    break
                for row in rows:
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
        """Extract Firefox history — one forensic event per moz_historyvisits row (if available),
        otherwise one per moz_places row that has a recorded last visit.

        Results are streamed in chunks of _FETCH_CHUNK rows — no LIMIT applied.
        """
        events = []
        try:
            # Check whether moz_historyvisits table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='moz_historyvisits';"
            )
            has_visits = cursor.fetchone() is not None

            if has_visits:
                # --- Primary path: one row per individual visit ---
                # visit_date is Unix epoch microseconds in moz_historyvisits
                cursor.execute("""
                    SELECT
                        p.url,
                        p.title,
                        p.visit_count,
                        h.visit_date
                    FROM moz_historyvisits h
                    INNER JOIN moz_places p ON p.id = h.place_id
                    WHERE h.visit_date IS NOT NULL
                    ORDER BY h.visit_date DESC
                """)
            else:
                # --- Fallback path: moz_places only, no LIMIT ---
                logger.debug("moz_historyvisits table not found — falling back to moz_places-only query.")
                cursor.execute("""
                    SELECT url, title, visit_count, last_visit_date
                    FROM moz_places
                    WHERE last_visit_date IS NOT NULL
                    ORDER BY last_visit_date DESC
                """)

            # Stream results in fixed-size chunks to keep memory flat
            while True:
                rows = cursor.fetchmany(_FETCH_CHUNK)
                if not rows:
                    break
                for row in rows:
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
