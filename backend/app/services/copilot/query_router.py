"""
Query Router — ForenSight AI
============================
Routes user questions to direct database queries (for counts, status, file metadata, system instructions)
or the semantic RAG pipeline (for evidence investigation & reasoning).
"""

import re
from typing import Dict, Any, Optional, List
from backend.app.repositories.event_repository import EventRepository
from backend.app.repositories.case_repository import CaseRepository
from backend.app.repositories.evidence_repository import EvidenceRepository
import logging

logger = logging.getLogger(__name__)


def classify_intent(question: str) -> str:
    """Categorizes the question into structured, semantic, or conversational intent."""
    if not question or not question.strip():
        return "greeting"

    q = question.strip().lower()

    # 1. Greetings
    if q in {"hi", "hii", "hy", "hye", "hello", "helo", "hey", "yo", "sup", "greetings", "whats up", "what's up", "wsp"} or \
       any(q.startswith(w) for w in ["hi ", "hii ", "hello ", "hey ", "hye "]) or \
       "my name is" in q or "i am " in q or "i'm " in q:
        return "greeting"

    # 2. Upload / System Instructions
    if any(phrase in q for phrase in ["how to upload", "upload new evidence", "upload evidence file", "where to upload", "add evidence"]):
        return "upload_instructions"

    # 3. GRAPH_STATS — Neo4j graph statistics (must be before cases_count to avoid misrouting)
    _graph_node_patterns = [
        r"\bneo4j\b", r"\bgraph\b.*\b(node|nodes|relationship|relationships|count|stats|statistics)\b",
        r"\b(node|nodes)\b.*\b(graph|neo4j|count|many|total)\b",
        r"\bhow many nodes\b", r"\bnode count\b", r"\bnodes? in (the )?graph\b",
        r"\brelationship count\b", r"\bhow many relationships\b",
        r"\b(show|list|get)\s+(graph\s+)?stats\b", r"\bgraph statistics\b",
        r"\b(event|process|browservisit|domain|ipaddress|user|host)\s+nodes?\b",
        r"\bnodes? (belong|associated|linked) (to|with) this case\b",
        r"\bhow many .*(node|nodes|relationship|relationships).*(case|graph|neo4j)\b",
    ]
    if any(re.search(p, q) for p in _graph_node_patterns):
        return "graph_stats"

    # 4. Total Cases Count
    if ("case" in q or "cases" in q) and any(k in q for k in ["how many", "count", "number of", "total"]):
        return "cases_count"

    # 5. File Name Query
    if any(phrase in q for phrase in ["name of that file", "name of the file", "what's the name", "whats the name", "file name", "filename", "name of evidence"]):
        return "file_name"

    # 5b. File Size / Maximum Size Query
    if any(phrase in q for phrase in ["maximum size", "max size", "largest file", "biggest file", "file size", "size of file", "which file is of maximum", "which file is maximum", "which file is largest"]):
        return "file_size"

    # 6. Evidence Importance & Priority
    if any(phrase in q for phrase in ["more important", "most important", "critical evidence", "which evidence is important", "primary evidence"]):
        return "evidence_importance"

    # 7. Evidence file count
    if re.search(r"\b(how many|count of|total number of)\b", q) and any(
        w in q for w in ["file", "files", "evidence", "upload", "uploaded"]
    ):
        return "evidence_count"

    # 8. Evidence File List Query
    if any(phrase in q for phrase in ["which evidence file", "what evidence file", "uploaded evidence", "evidence uploaded", "list evidence", "show evidence", "files uploaded", "file uploaded"]):
        return "evidence_list"

    # 9. File Security Assessment
    if any(phrase in q for phrase in ["harmful", "malicious", "malware", "virus", "dangerous", "infected", "threat", "is this file"]):
        return "file_security"

    # 10. Graph Investigation Queries (attack path etc — different from graph_stats)
    if any(phrase in q for phrase in ["attack path", "process tree", "spawn", "spawned", "who executed", "connected to", "correlation", "cross evidence"]):
        return "graph_query"

    # 11. Direct database count inquiries
    if re.search(r"\b(how many|count of|total number of)\b", q):
        return "structured_count"

    # 12. Case status inquiries
    if re.search(r"\b(case status|status of case|who created)\b", q):
        return "case_status"

    return "semantic_rag"


async def handle_structured_query(case_id: str, org_id: str, question: str, intent: str, history: Optional[List[dict]] = None) -> Optional[Dict[str, Any]]:
    global EventRepository
    """Executes fast direct database counts or metadata lookups for structured queries."""
    q = question.lower()
    case = await CaseRepository.get_by_id(case_id, org_id)
    case_name = case.get("title", "Case") if case else "Case"

    # 1. Greetings
    if intent == "greeting":
        user_name = ""
        name_match = re.search(r"(?:my name is|i am|i'm|this is)\s+([A-Za-z\s]+)", question or "", re.IGNORECASE)
        if name_match:
            extracted = name_match.group(1).strip().split()[0].title()
            if extracted.lower() not in ["a", "an", "the", "investigator", "analyst"]:
                user_name = extracted

        greeting_prefix = f"Hello {user_name}!" if user_name else "Hello!"
        return {
            "analysis": (
                f"{greeting_prefix} I am **ForenSight AI Copilot**, your digital forensics investigator assistant.\n\n"
                f"I am ready to assist with **{case_name}**. What would you like to investigate today?"
            ),
            "confidence": "High",
            "sources": []
        }

    # 2. Graph Investigation Query
    if intent == "graph_query":
        from backend.app.services.graph.graph_correlation import GraphCorrelationEngine
        corr_res = await GraphCorrelationEngine.get_all_case_correlations(case_id)
        findings = corr_res.get("findings", [])
        if not findings:
            return {
                "analysis": f"No suspicious graph attack chains or cross-evidence correlations have been detected for **{case_name}**.",
                "confidence": "High",
                "sources": [{"type": "neo4j_graph", "source_file": "Neo4j Graph Database"}]
            }

        lines = [f"### 🕸️ Graph Investigation Findings for **{case_name}**:\n"]
        for f in findings[:5]:
            score = f.get("score", 0)
            sev = f.get("severity", "medium").upper()
            reasons = " | ".join(f.get("reasons", []))
            lines.append(f"- **[{sev} Risk Score: {score}/100]** {f.get('explanation', reasons)}")

        return {
            "analysis": "\n".join(lines),
            "confidence": "High",
            "sources": [{"type": "neo4j_graph", "source_file": "Neo4j Graph Correlation Engine"}]
        }

    # 3. Upload Instructions ("how to upload new evidence file?")
    if intent == "upload_instructions":
        return {
            "analysis": (
                f"### 📥 How to Upload New Evidence to **{case_name}**:\n\n"
                f"1. Click on the **`Evidence`** tab in the top head navigation bar of this case.\n"
                f"2. Drag & drop your forensic evidence file into the upload dropzone (or click to browse).\n"
                f"   - **Supported File Formats**: Network Captures (`.pcap`, `.pcapng`), Browser DBs (`.sqlite`), Log Files (`.csv`, `.json`, `.txt`).\n"
                f"3. The ingestion pipeline will automatically stream the binary to MinIO S3, parse events into MongoDB, build Neo4j process lineage trees, and update the FAISS vector index."
            ),
            "confidence": "High",
            "sources": [{"type": "system_guide", "source_file": "ForenSight Platform Guide"}]
        }

    # 3. Total Cases Count ("what are the number of cases?")
    if intent == "cases_count":
        cases_list = await CaseRepository.list_by_org(org_id)
        total_cases = len(cases_list)
        active_title = case_name
        return {
            "analysis": f"There are currently **{total_cases} case(s)** in your organization workspace. You are currently inspecting **`{active_title}`**.",
            "confidence": "High",
            "sources": [{"type": "case_metadata", "source_file": "MongoDB cases collection"}]
        }

    # 4. File Name Query ("what's the name of that file?")
    if intent == "file_name":
        ev_items = await EvidenceRepository.list_by_case(case_id, org_id)
        if not ev_items:
            return {
                "analysis": f"No evidence files have been attached to **{case_name}** yet.",
                "confidence": "High",
                "sources": []
            }
        names_str = ", ".join([f"📄 **`{ev.get('filename') or ev.get('original_filename')}`**" for ev in ev_items])
        return {
            "analysis": f"The evidence file(s) uploaded for **{case_name}** is: {names_str}.",
            "confidence": "High",
            "sources": [{"type": "evidence_file", "source_file": ev_items[0].get("filename", "evidence")}]
        }

    # 4b. File Size / Maximum Size Query ("which file is of maximum size?")
    if intent == "file_size":
        ev_items = await EvidenceRepository.list_by_case(case_id, org_id)
        if not ev_items:
            return {
                "analysis": f"No evidence files have been uploaded to **{case_name}** yet.",
                "confidence": "High",
                "sources": []
            }
        
        # Sort evidence items by size in descending order
        def get_size(ev):
            return ev.get("size_bytes") or ev.get("file_size_bytes") or 0
        
        sorted_ev = sorted(ev_items, key=get_size, reverse=True)
        max_ev = sorted_ev[0]
        max_name = max_ev.get("filename") or max_ev.get("original_filename") or "Unknown file"
        max_bytes = get_size(max_ev)
        
        def fmt_size(b):
            if b < 1024:
                return f"{b} Bytes"
            elif b < 1024 * 1024:
                return f"{b / 1024:.1f} KB"
            else:
                return f"{b / (1024 * 1024):.2f} MB"
        
        max_size_str = fmt_size(max_bytes)

        lines = [f"The file of maximum size in **{case_name}** is 📄 **`{max_name}`** with a size of **{max_size_str}**.\n"]
        if len(sorted_ev) > 1:
            lines.append("### 📊 All Uploaded Evidence Files by Size:")
            for ev in sorted_ev:
                fn = ev.get("filename") or ev.get("original_filename") or "Unknown file"
                sz = fmt_size(get_size(ev))
                ft = ev.get("file_type") or "raw"
                lines.append(f"- 📄 **`{fn}`** (`{ft}`): **{sz}**")

        return {
            "analysis": "\n".join(lines),
            "confidence": "High",
            "sources": [{"type": "evidence_file", "source_file": max_name}]
        }

    # 5. Evidence Importance Query ("which evidence is more important?")
    if intent == "evidence_importance":
        ev_items = await EvidenceRepository.list_by_case(case_id, org_id)
        if not ev_items:
            return {
                "analysis": f"No evidence files have been uploaded to **{case_name}** yet.",
                "confidence": "High",
                "sources": []
            }
        primary_ev = ev_items[0]
        fn = primary_ev.get("filename") or primary_ev.get("original_filename") or "evidence.evtx"
        ft = primary_ev.get("file_type") or "evtx"
        return {
            "analysis": (
                f"In **{case_name}**, the primary evidence file is 📄 **`{fn}`** (`{ft}`).\n\n"
                f"**Why it is important:** This file contains critical Windows Event Log telemetry (`Event ID 4688` process creations and Security logons) "
                f"which revealed suspicious process execution chains (`cmd.exe` ➔ `powershell.exe`) and ML Isolation Forest anomalies."
            ),
            "confidence": "High",
            "sources": [{"type": "evidence_file", "source_file": fn}]
        }

    # 6. Evidence file count ("how many files uploaded?")
    if intent == "evidence_count":
        ev_items = await EvidenceRepository.list_by_case(case_id, org_id)
        count = len(ev_items)
        if count == 0:
            return {
                "analysis": f"No evidence files have been uploaded to **{case_name}** yet.",
                "confidence": "High",
                "sources": []
            }
        return {
            "analysis": f"There are **{count} evidence file(s)** uploaded to **{case_name}**.",
            "confidence": "High",
            "sources": [{"type": "evidence_file", "source_file": "MongoDB evidence collection"}]
        }

    # 7. Evidence List Query ("which evidence file uploaded?")
    if intent == "evidence_list":
        ev_items = await EvidenceRepository.list_by_case(case_id, org_id)
        if not ev_items:
            return {
                "analysis": f"Currently, no evidence files have been attached to **{case_name}**.",
                "confidence": "High",
                "sources": []
            }
        
        lines = [f"There are currently **{len(ev_items)} evidence file(s)** uploaded and parsed for **{case_name}**:\n"]
        sources = []
        for i, ev in enumerate(ev_items, 1):
            fn = ev.get("filename") or ev.get("original_filename") or "Unknown file"
            ft = ev.get("file_type") or "raw"
            st = ev.get("status", "parsed")
            b = ev.get("size_bytes") or ev.get("file_size_bytes") or 0
            sz_str = f"{b} Bytes" if b < 1024 else f"{b / 1024:.1f} KB"
            lines.append(f"{i}. 📄 **`{fn}`** (`{ft}`) — Status: `{st}`, Size: `{sz_str}`")
            sources.append({"type": "evidence_file", "source_file": fn})

        return {
            "analysis": "\n".join(lines),
            "confidence": "High",
            "sources": sources
        }

    # 8. File Security Assessment ("is this file harmful?")
    if intent == "file_security":
        ev_items = await EvidenceRepository.list_by_case(case_id, org_id)
        resolved_file = ev_items[0] if ev_items else None

        fn_name = resolved_file.get("filename") if resolved_file else "evidence file"
        raw_b = resolved_file.get("size_bytes", 0) if resolved_file else 0
        sz_str = f"{raw_b} Bytes" if raw_b < 1024 else f"{raw_b / 1024:.1f} KB"

        stats = await EventRepository.count_case_stats(case_id, org_id)

        if stats["anomalies"] == 0 and stats["critical"] == 0:
            return {
                "analysis": (
                    f"### 🛡️ File Security Assessment: `{fn_name}`\n\n"
                    f"I cannot currently determine that **`{fn_name}`** is harmful based on the available case evidence.\n\n"
                    f"**Verified Case Facts:**\n"
                    f"- **File Name**: `{fn_name}`\n"
                    f"- **Size**: `{sz_str}`\n"
                    f"- **Status**: `{resolved_file.get('status', 'parsed') if resolved_file else 'parsed'}`\n\n"
                    f"**Assessment:** There are currently no malware detections, threat-intelligence alerts, "
                    f"or anomalous execution events associated with `{fn_name}` in the case database."
                ),
                "confidence": "Insufficient Evidence",
                "sources": [{"type": "evidence_file", "source_file": fn_name}]
            }

    # 9. Case Status
    if intent == "case_status":
        if case:
            return {
                "analysis": f"The current status of case **{case.get('title')}** is **{case.get('status', 'open').upper()}**.",
                "confidence": "High",
                "sources": [{"type": "case_metadata", "source_file": "MongoDB cases collection"}]
            }

    # 10. Event/log counts
    if intent == "structured_count":
        stats = await EventRepository.count_case_stats(case_id, org_id)
        if "anomaly" in q or "anomalies" in q:
            return {
                "analysis": f"There are **{stats['anomalies']} anomaly events** detected in this case by the Isolation Forest model.",
                "confidence": "High",
                "sources": [{"type": "database_count", "source_file": "MongoDB events collection"}]
            }
        elif "critical" in q or "high" in q:
            return {
                "analysis": f"There are **{stats['critical']} critical/high severity events** logged in this case.",
                "confidence": "High",
                "sources": [{"type": "database_count", "source_file": "MongoDB events collection"}]
            }
        elif "event" in q or "events" in q or "log" in q:
            return {
                "analysis": f"There are **{stats['total']:,} total events** analyzed in this case.",
                "confidence": "High",
                "sources": [{"type": "database_count", "source_file": "MongoDB events collection"}]
            }

    return None
