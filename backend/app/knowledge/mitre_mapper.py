from typing import Dict, Any

class MitreMapper:
    MAPPINGS = {
        "powershell.exe": {
            "tactic": "Execution",
            "technique_id": "T1059.001",
            "technique_name": "PowerShell",
            "description": "Adversaries may use PowerShell to execute commands and scripts."
        },
        "mimikatz.exe": {
            "tactic": "Credential Access",
            "technique_id": "T1003",
            "technique_name": "OS Credential Dumping",
            "description": "Adversaries may dump credentials to obtain security details."
        },
        "schtasks.exe": {
            "tactic": "Persistence",
            "technique_id": "T1053",
            "technique_name": "Scheduled Task/Job",
            "description": "Adversaries may abuse scheduling tasks to execute malicious payloads persistently."
        },
        "whoami.exe": {
            "tactic": "Discovery",
            "technique_id": "T1033",
            "technique_name": "System Owner/User Discovery",
            "description": "Adversaries may attempt to identify the username of the active system owner."
        }
    }

    @classmethod
    def map_event_to_ttp(cls, event: Dict[str, Any]) -> Dict[str, Any]:
        """Map event subject/object attributes to MITRE ATT&CK techniques."""
        subject = str(event.get("subject", "")).lower()
        obj = str(event.get("object", "")).lower()
        
        # Check both subject and object context fields
        for key, ttp in cls.MAPPINGS.items():
            if key in subject or key in obj:
                return {
                    "mapped": True,
                    "tactic": ttp["tactic"],
                    "technique_id": ttp["technique_id"],
                    "technique_name": ttp["technique_name"],
                    "description": ttp["description"]
                }
        return {"mapped": False}
