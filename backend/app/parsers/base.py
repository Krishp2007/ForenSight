from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseParser(ABC):
    """Abstract base class that all forensic evidence parsers must implement."""

    @abstractmethod
    def parse(self, file_content: bytes, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parse raw evidence file content bytes and return a list of normalized events.
        
        Args:
            file_content: Raw byte content of the file from MinIO.
            filename: Optional original filename to assist in parsing logic or metadata.

        Returns:
            A list of dictionaries. Each dictionary must conform to the EventBase structure:
            {
                "timestamp": datetime,
                "event_type": EventType,
                "source": EventSource,
                "severity": EventSeverity,
                "subject": str,
                "action": str,
                "object": str,
                "details": Dict[str, Any],
                "mitre_techniques": List[str]
            }
        """
        pass
