from typing import List, Dict, Any

class ForensicRuleFilter:
    NOISY_SUBJECTS = ["explorer.exe", "ntoskrnl.exe"]
    NOISY_ACTIONS = ["gui_refresh", "read"]

    @classmethod
    def filter_noisy_telemetry(cls, raw_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out benign OS events and keep critical security indicators."""
        filtered = []
        for e in raw_events:
            if not cls.should_ignore(e):
                filtered.append(e)
        return filtered

    @classmethod
    def should_ignore(cls, event: Dict[str, Any]) -> bool:
        """Heuristic check to determine if an event represents common benign telemetry noise."""
        subj = str(event.get("subject", "")).lower()
        act = str(event.get("action", "")).lower()
        sev = str(event.get("severity", "info")).lower()
        
        # Suppress benign noise from standard background system services/shells
        is_noisy_subj = any(ns in subj for ns in cls.NOISY_SUBJECTS)
        is_noisy_act = any(na in act for na in cls.NOISY_ACTIONS)
        
        if (is_noisy_subj or is_noisy_act) and sev == "info":
            return True
        return False
