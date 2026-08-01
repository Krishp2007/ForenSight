"""
MITRE ATT&CK Mapper — ForenSight AI
======================================
Architecture Section 5.5 reference: "A library of hand-written rules…
Each rule reads a pattern, asserts a derived relation, and records its
provenance." — this module handles the MITRE technique tagging layer.

Centralizes all MITRE ATT&CK technique assignments so that:
  - Every parser imports from here instead of hardcoding strings
  - New technique mappings are added in one place
  - The copilot and report can describe techniques by name, not just ID

Covers the technique IDs used across all ForenSight parsers:
  evtx_parser, pcap_parser, browser_parser, csv_parser, json_parser

Reference: https://attack.mitre.org/
"""

from typing import List, Optional


# ── Technique Registry ────────────────────────────────────────────────────────
# Maps technique ID → { name, tactic, description }
TECHNIQUE_REGISTRY: dict = {

    # Execution
    "T1059":     {"name": "Command and Scripting Interpreter", "tactic": "Execution",
                  "description": "Adversaries may abuse command and script interpreters to execute commands, scripts, or binaries."},
    "T1059.001": {"name": "PowerShell", "tactic": "Execution",
                  "description": "Adversaries may abuse PowerShell commands and scripts for execution, including encoded commands (-enc)."},
    "T1059.003": {"name": "Windows Command Shell", "tactic": "Execution",
                  "description": "Adversaries may abuse the Windows command shell (cmd.exe) to execute commands."},
    "T1204":     {"name": "User Execution", "tactic": "Execution",
                  "description": "An adversary may rely upon specific actions by a user to gain execution."},

    # Persistence
    "T1547":     {"name": "Boot or Logon Autostart Execution", "tactic": "Persistence",
                  "description": "Adversaries may configure system settings to automatically execute a program during system boot or logon."},
    "T1547.001": {"name": "Registry Run Keys / Startup Folder", "tactic": "Persistence",
                  "description": "Adversaries may add programs to the Run/RunOnce keys to cause them to execute on system startup."},

    # Privilege Escalation
    "T1055":     {"name": "Process Injection", "tactic": "Privilege Escalation",
                  "description": "Adversaries may inject code into processes to evade process-based defenses and elevate privileges."},

    # Defense Evasion
    "T1070":     {"name": "Indicator Removal", "tactic": "Defense Evasion",
                  "description": "Adversaries may delete or alter artifacts generated on a system to remove evidence."},
    "T1027":     {"name": "Obfuscated Files or Information", "tactic": "Defense Evasion",
                  "description": "Adversaries may attempt to make an executable or file difficult to discover or analyze."},

    # Credential Access
    "T1110":     {"name": "Brute Force", "tactic": "Credential Access",
                  "description": "Adversaries may use brute force techniques to gain access to accounts via repeated authentication attempts."},
    "T1555":     {"name": "Credentials from Password Stores", "tactic": "Credential Access",
                  "description": "Adversaries may search for common password storage locations to obtain user credentials."},
    "T1539":     {"name": "Steal Web Session Cookie", "tactic": "Credential Access",
                  "description": "Adversaries may steal web application or service session cookies."},

    # Discovery
    "T1033":     {"name": "System Owner/User Discovery", "tactic": "Discovery",
                  "description": "Adversaries may attempt to find the primary user, currently logged-in user, or set of users."},
    "T1082":     {"name": "System Information Discovery", "tactic": "Discovery",
                  "description": "An adversary may attempt to get detailed information about the operating system and hardware."},
    "T1087":     {"name": "Account Discovery", "tactic": "Discovery",
                  "description": "Adversaries may attempt to get a listing of accounts on a system or within an environment."},
    "T1057":     {"name": "Process Discovery", "tactic": "Discovery",
                  "description": "Adversaries may attempt to get information about running processes on a system."},
    "T1049":     {"name": "System Network Connections Discovery", "tactic": "Discovery",
                  "description": "Adversaries may attempt to get a listing of network connections to or from a compromised system."},

    # Lateral Movement
    "T1021":     {"name": "Remote Services", "tactic": "Lateral Movement",
                  "description": "Adversaries may use remote services to initially access or move laterally through the network."},

    # Collection
    "T1005":     {"name": "Data from Local System", "tactic": "Collection",
                  "description": "Adversaries may search local system sources to find files of interest."},
    "T1185":     {"name": "Browser Session Hijacking", "tactic": "Collection",
                  "description": "Adversaries may take advantage of security vulnerabilities and inherent functionality in browser software."},

    # Command and Control
    "T1043":     {"name": "Commonly Used Port", "tactic": "Command and Control",
                  "description": "Adversaries may communicate over a commonly used port to bypass firewalls or blend in with traffic."},
    "T1071":     {"name": "Application Layer Protocol", "tactic": "Command and Control",
                  "description": "Adversaries may communicate using application layer protocols to avoid detection."},
    "T1090":     {"name": "Proxy", "tactic": "Command and Control",
                  "description": "Adversaries may use a connection proxy to direct traffic."},
    "T1090.003": {"name": "Multi-hop Proxy / Tor", "tactic": "Command and Control",
                  "description": "Adversaries may chain together multiple proxies (including Tor) to disguise origin."},
    "T1219":     {"name": "Remote Access Software", "tactic": "Command and Control",
                  "description": "An adversary may use legitimate remote access software to establish an interactive C2 channel."},

    # Exfiltration
    "T1041":     {"name": "Exfiltration Over C2 Channel", "tactic": "Exfiltration",
                  "description": "Adversaries may steal data by exfiltrating it over an existing C2 channel."},
    "T1567":     {"name": "Exfiltration Over Web Service", "tactic": "Exfiltration",
                  "description": "Adversaries may use an existing web service as a means to exfiltrate data."},

    # Impact
    "T1486":     {"name": "Data Encrypted for Impact", "tactic": "Impact",
                  "description": "Adversaries may encrypt data on target systems to interrupt availability (ransomware)."},
    "T1489":     {"name": "Service Stop", "tactic": "Impact",
                  "description": "Adversaries may stop or disable services on a system to render it unable to provide those services."},
}


# ── Keyword-to-Technique mapping for dynamic tagging ─────────────────────────
# Used by parsers that receive unstructured text (CSV, JSON, browser)
KEYWORD_MAP: list = [
    # (keyword_in_lower, [technique_ids])
    ("powershell",          ["T1059.001"]),
    ("-encodedcommand",     ["T1059.001"]),
    ("-enc ",               ["T1059.001"]),
    ("cmd.exe",             ["T1059.003"]),
    ("whoami",              ["T1033"]),
    ("net user",            ["T1087"]),
    ("net localgroup",      ["T1087"]),
    ("ipconfig",            ["T1082"]),
    ("systeminfo",          ["T1082"]),
    ("tasklist",            ["T1057"]),
    ("netstat",             ["T1049"]),
    ("mimikatz",            ["T1555"]),
    ("lsass",               ["T1055"]),
    ("currentversion\\run", ["T1547.001"]),
    ("runonce",             ["T1547.001"]),
    ("startup folder",      ["T1547.001"]),
    (".onion",              ["T1090.003"]),
    ("tor",                 ["T1090.003"]),
    ("4444",                ["T1043"]),
    ("1337",                ["T1043"]),
    ("6667",                ["T1043"]),
    ("8080",                ["T1043"]),
    ("failed logon",        ["T1110"]),
    ("brute",               ["T1110"]),
    ("cookie",              ["T1539"]),
    ("session",             ["T1185"]),
    ("download",            ["T1005"]),
    ("ransomware",          ["T1486"]),
    ("encrypt",             ["T1486"]),
    ("exfil",               ["T1041"]),
    ("upload",              ["T1567"]),
    ("rdp",                 ["T1021"]),
    ("winrm",               ["T1021"]),
    ("wmic",                ["T1059.003"]),
    ("wscript",             ["T1059"]),
    ("cscript",             ["T1059"]),
    ("regsvr32",            ["T1027"]),
    ("certutil",            ["T1027"]),
    ("bitsadmin",           ["T1071"]),
    ("mshta",               ["T1059"]),
    ("rundll32",            ["T1027"]),
    ("schtasks",            ["T1547"]),
    ("at.exe",              ["T1547"]),
    ("sc.exe",              ["T1489"]),
    ("net stop",            ["T1489"]),
    ("vssadmin",            ["T1070"]),
    ("bcdedit",             ["T1070"]),
    ("wevtutil",            ["T1070"]),
]


class MitreMapper:
    """
    Centralized MITRE ATT&CK technique tagger.
    All parsers should use this instead of hardcoding technique IDs.
    """

    @staticmethod
    def get_technique(technique_id: str) -> Optional[dict]:
        """Look up a technique by ID. Returns full metadata dict or None."""
        return TECHNIQUE_REGISTRY.get(technique_id)

    @staticmethod
    def get_technique_name(technique_id: str) -> str:
        """Return human-readable technique name, or the raw ID if unknown."""
        t = TECHNIQUE_REGISTRY.get(technique_id)
        return t["name"] if t else technique_id

    @staticmethod
    def get_tactic(technique_id: str) -> str:
        """Return the tactic name for a technique ID."""
        t = TECHNIQUE_REGISTRY.get(technique_id)
        return t["tactic"] if t else "Unknown"

    @staticmethod
    def describe(technique_id: str) -> str:
        """Return short description for a technique."""
        t = TECHNIQUE_REGISTRY.get(technique_id)
        return t["description"] if t else f"No description for {technique_id}"

    @staticmethod
    def tag_from_text(text: str) -> List[str]:
        """
        Scan arbitrary lowercase text and return all matching technique IDs.
        Used by CSV/JSON parsers that don't have structured event IDs.

        Example:
            tag_from_text("powershell -enc abc123 whoami") 
            → ["T1059.001", "T1033"]
        """
        text_lower = text.lower()
        found = []
        seen = set()
        for keyword, techniques in KEYWORD_MAP:
            if keyword in text_lower:
                for t in techniques:
                    if t not in seen:
                        found.append(t)
                        seen.add(t)
        return found

    @staticmethod
    def tag_from_event_id(event_id: int) -> List[str]:
        """
        Map a Windows Event ID directly to MITRE technique IDs.
        Used by the EVTX parser for precise technique assignment.
        """
        mapping = {
            4625: ["T1110"],          # Failed logon → Brute Force
            4688: ["T1059"],          # Process creation → Command Interpreter
            4697: ["T1543"],          # Service installed
            4698: ["T1053"],          # Scheduled task created
            4702: ["T1053"],          # Scheduled task updated
            4720: ["T1136"],          # User account created
            4726: ["T1531"],          # User account deleted
            4732: ["T1098"],          # Member added to local group
            4657: ["T1547.001"],      # Registry value modified
            5039: ["T1547.001"],      # Registry key renamed
            4663: ["T1005"],          # Object access
            4660: ["T1070"],          # Object deleted
            4776: ["T1110"],          # NTLM auth attempted
            1102: ["T1070"],          # Audit log cleared
            4104: ["T1059.001"],      # PowerShell script block
        }
        return mapping.get(event_id, [])

    @staticmethod
    def enrich_techniques(technique_ids: List[str]) -> List[dict]:
        """
        Convert a list of technique IDs into full metadata objects.
        Used by the report generator to render technique detail tables.

        Returns:
            [{"id": "T1059.001", "name": "PowerShell", "tactic": "Execution", ...}]
        """
        result = []
        for tid in technique_ids:
            meta = TECHNIQUE_REGISTRY.get(tid, {})
            result.append({
                "id": tid,
                "name": meta.get("name", tid),
                "tactic": meta.get("tactic", "Unknown"),
                "description": meta.get("description", ""),
                "url": f"https://attack.mitre.org/techniques/{tid.replace('.', '/')}",
            })
        return result
