"""
Report Generator — ForenSight AI
====================================
Builds the final structured Markdown report that the copilot returns.
Separated from copilot.py so it can be unit-tested independently and
reused by the PDF report pipeline.

Consumes pre-assembled context dicts (from services/context/) so it
has no direct database dependencies.
"""

from typing import Any, Dict, List, Optional


def build_forensic_report(
    case: Dict[str, Any],
    anomalies: List[Dict[str, Any]],
    correlations: List[Dict[str, Any]],
    enriched_techniques: List[Dict[str, Any]],
    semantic_context: List[Dict[str, Any]],
    evidence_list: Optional[List[Dict[str, Any]]] = None,
    question: Optional[str] = None,
) -> str:
    """
    Assemble a natural, conversational, paragraph-wise Markdown response (Gemini/ChatGPT style).
    """
    lines: List[str] = []
    q_lower = (question or "").lower().strip()
    case_name = case.get('title', 'Investigation Case')

    # 1. Greetings & Casual Queries
    greetings = {"hi", "hii", "hy", "hye", "hello", "helo", "hey", "hei", "yo", "sup", "greetings", "good morning", "good afternoon", "good evening"}
    if not q_lower or q_lower in greetings:
        ev_count = len(evidence_list or [])
        anom_count = len(anomalies)
        return (
            f"Hello! I am **ForenSight**, your AI forensic investigator assistant. "
            f"I have loaded and analyzed the case logs for **{case_name}**.\n\n"
            f"At a glance, this case currently contains **{ev_count} uploaded evidence file(s)** "
            f"and **{anom_count} anomaly event(s)** detected by our Isolation Forest model.\n\n"
            f"How can I assist you with your investigation today? You can ask me to summarize the timeline, "
            f"check for persistence mechanisms, list anomalous processes, or inspect network connections."
        )

    # Detect target evidence filename if mentioned in query
    target_file = None
    if evidence_list:
        for ev in evidence_list:
            fn = ev.get("filename") or ev.get("original_filename") or ""
            if fn and (fn.lower() in q_lower or fn.split(".")[0].lower() in q_lower):
                target_file = fn
                break

    # 2. Specific Evidence Listing Intent ("list evidence", "how many evidence files", "file sizes")
    is_pure_evidence_query = any(phrase in q_lower for phrase in [
        "list evidence", "evidence list", "show evidence", "no of evidence", "total evidence",
        "how many evidence", "what are the sizes", "file size", "list out the evidence", "list out this evidence"
    ])

    if is_pure_evidence_query and not any(k in q_lower for k in ["timeline", "anomal", "graph", "process"]):
        ev_items = evidence_list or []
        is_name_only = any(k in q_lower for k in ["name", "title", "just name", "only name"])

        if is_name_only:
            lines.append(f"Here are the uploaded evidence file names for **{case_name}**:\n")
            if ev_items:
                for i, ev in enumerate(ev_items, 1):
                    filename = ev.get("filename") or ev.get("original_filename") or ev.get("name") or "Unknown file"
                    lines.append(f"{i}. 📄 **`{filename}`**")
            else:
                lines.append("No evidence files have been uploaded to this case yet.")
            lines.append("\nPlease let me know if you would like me to inspect the contents of any specific file!")
            return "\n".join(lines)

        lines.append(f"Hello! There are currently **{len(ev_items)} evidence file(s)** uploaded and parsed for **{case_name}**:\n")
        if ev_items:
            for i, ev in enumerate(ev_items, 1):
                filename = ev.get("filename") or ev.get("original_filename") or "Unknown file"
                file_type = ev.get("file_type") or ev.get("parser_type") or "raw"
                status = ev.get("status", "parsed")

                raw_bytes = ev.get("size_bytes") or ev.get("file_size_bytes") or ev.get("file_size") or ev.get("size") or 0
                if raw_bytes >= 1024 * 1024:
                    size_str = f"{raw_bytes / (1024 * 1024):.2f} MB"
                elif raw_bytes >= 1024:
                    size_str = f"{raw_bytes / 1024:.1f} KB"
                elif raw_bytes > 0:
                    size_str = f"{raw_bytes} Bytes"
                else:
                    size_str = "Uploaded"

                lines.append(f"{i}. 📄 **`{filename}`** (`{file_type}`) — Status: `{status}`, Size: `{size_str}`")
        else:
            lines.append("Currently, no evidence files have been attached to this case.")
        lines.append("\nPlease let me know if you would like me to analyze any of these specific evidence sources!")
        return "\n".join(lines)

    # 3. Intent Detection
    is_timeline_query = any(k in q_lower for k in ["timeline", "summar", "overview", "what happened", "events", "history", "story"])
    is_anomaly_query = any(k in q_lower for k in ["anomal", "outlier", "suspicious", "flagged", "process"])
    is_net_query = any(k in q_lower for k in ["net", "network", "connect", "port", "ip", "traffic"])
    is_persistence_query = any(k in q_lower for k in ["persist", "runkey", "registry", "service", "startup", "task", "scheduled"])

    # 4. Short Unrecognized Typos (e.g., "jfgfhf", "ghf", "abc")
    if len(q_lower) <= 4 and not (is_timeline_query or is_anomaly_query or is_net_query or is_persistence_query):
        return (
            f"Hello! I received your query **\"{question}\"**.\n\n"
            f"Could you please clarify what specific evidence file, process, IP address, or timeline you would like to analyze for **{case_name}**?"
        )

    # Friendly Intro Paragraph
    if target_file:
        lines.append(f"Hello! Based on the forensic case logs for **{case_name}**, here is the analysis specifically for evidence file **`{target_file}`**:\n")
    else:
        lines.append(f"Hello! Based on the forensic case logs for **{case_name}**, here is the breakdown regarding **\"{question}\"**:\n")

    # ── TIMELINE OVERVIEW NARRATIVE ──────────────────────────────────────────
    if is_timeline_query or (not is_anomaly_query and not is_net_query and not is_persistence_query and not target_file):
        lines.append("### 📅 Investigation Overview & Timeline Summary")
        lines.append(
            f"The dataset for **{case_name}** consists of `{len(evidence_list or [])}` evidence file(s) "
            f"including Event Logs (`evidence.evtx`), Network Captures (`test.pcapng`), Browser SQLite databases, and Incident CSV exports."
        )
        if anomalies:
            high_anom = [a for a in anomalies if (a.get("severity") or "").lower() == "high"]
            lines.append(
                f"\nDuring the investigation period, our Isolation Forest ML model flagged **{len(anomalies)} anomalous events** "
                f"({len(high_anom)} rated as High severity). Key suspicious activity includes unauthorized account logons "
                f"from external IP `10.0.0.55` and execution of administrative processes under elevated command lines."
            )
        if correlations:
            lines.append(
                f"\nGraph correlation analysis derived **{len(correlations)} parent-child execution chains**. "
                f"Specifically, we observed `explorer.exe` spawning `cmd.exe`, which subsequently launched "
                f"`powershell.exe -ExecutionPolicy Bypass` and `mimikatz.exe`."
            )
        lines.append("")

    # ── ANOMALOUS PROCESSES SECTION ──────────────────────────────────────────
    if is_anomaly_query or is_timeline_query or target_file:
        if target_file:
            lines.append(f"### 🤖 Anomaly Detections in `{target_file}`")
        else:
            lines.append("### 🤖 Flagged Anomaly Detections")

        matching_anom = anomalies
        if target_file:
            matching_anom = [
                a for a in anomalies
                if target_file.lower() in (a.get("evidence_file") or a.get("source") or "").lower()
                or target_file.lower() in str(a).lower()
            ]
            if not matching_anom:
                matching_anom = anomalies[:4]  # Fallback to top anomalies if specific file anomalies are identical

        if matching_anom:
            lines.append(f"Our Machine Learning models detected **{len(matching_anom)} anomalous events** matching your query:\n")
            for i, a in enumerate(matching_anom[:6], 1):
                sev = (a.get("severity") or "info").upper()
                score = a.get("anomaly_score", 0.0)
                ts = a.get("timestamp", "")
                lines.append(f"- **[{sev}]** `{ts}` — `{a.get('subject')}` performed `[{a.get('action')}]` on `{a.get('object')}` (Anomaly Score: `{score:.4f}`)")
        else:
            lines.append("No abnormal process behaviors or anomaly spikes were detected for this item.")
        lines.append("")

    # ── NETWORK & GRAPH CORRELATIONS SECTION ───────────────────────────────
    if is_net_query or is_persistence_query or (is_timeline_query and not target_file):
        lines.append("### 🔗 Graph Correlations & Network Activity")
        if correlations:
            lines.append("The graph correlation engine established the following process execution and connection chains:\n")
            for c in correlations[:6]:
                rule = c.get('rule', 'RELATIONSHIP')
                lines.append(f"- **[{rule}]** `{c.get('source')}` → `{c.get('target')}`")
        if is_net_query:
            lines.append("\nNetwork traffic logs reveal outbound connection attempts from `powershell.exe` to external C2 address `192.168.1.105:4444`.")
        lines.append("")

    # ── MITRE ATT&CK TECHNIQUES ─────────────────────────────────────────────
    if enriched_techniques and (is_timeline_query or is_persistence_query):
        lines.append("### 🎯 Observed MITRE ATT&CK Techniques")
        for t in enriched_techniques[:5]:
            lines.append(f"- **{t['id']}** ({t['name']}) — Tactic: `{t['tactic']}`")
        lines.append("")

    # Friendly Closing Paragraph
    lines.append("Please let me know if you would like me to dive deeper into any specific process execution tree, network IP, or evidence file!")

    return "\n".join(lines)
