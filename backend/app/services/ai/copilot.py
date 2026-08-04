"""
Copilot Service — ForenSight AI
==================================
Orchestrates the full RAG pipeline:
  1. Build context via ContextBuilder (intent routing + all retrievals)
  2. Build the prompt string
  3. Route to the configured LLM provider (Gemini → Ollama → local fallback)
  4. Return markdown response

Architecture Section 5.6 — AI Copilot Layer.
"""

import logging
import os
from typing import Optional, List, Any

from backend.app.config import settings
from backend.app.services.context.context_builder import build_copilot_context
from backend.app.services.copilot.query_router import classify_intent, handle_structured_query
from backend.app.services.copilot.report_generator import build_forensic_report

logger = logging.getLogger(__name__)


def _build_prompt(ctx: dict) -> str:
    """Assemble the LLM prompt from the assembled context dict."""
    case = ctx["case"]
    anomalies = ctx["anomalies"]
    correlations = ctx["correlations"]
    enriched_techniques = ctx["enriched_techniques"]
    semantic_context = ctx["semantic_context"]
    timeline_ctx = ctx.get("timeline_ctx", {})
    question = ctx.get("question")
    intent = ctx.get("intent", "summarise")

    lines = [
        "You are ForenSight, an expert AI digital forensics assistant.",
        "Your task is to answer the investigator's question using the provided context.",
        "",
        "CRITICAL OUTPUT FORMAT RULES:",
        "1. Output ONLY your final clean, professional Markdown response.",
        "2. Do NOT repeat, echo, or quote prompt rules, constraints, tasks, roles, or internal reasoning steps.",
        "3. Keep the answer direct, concise, and focused strictly on what was asked.",
        "4. Format timestamps in UTC ISO-8601.",
        "",
        f"Case Title: {case.get('title')}",
        f"Case Description: {case.get('description', 'N/A')}",
        f"Case Status: {case.get('status', 'open')}",
    ]

    if question:
        lines.append(f"\nInvestigator question: \"{question}\"")

    # Uploaded evidence list
    evidence_list = ctx.get("evidence_list", [])
    if evidence_list:
        lines.append("\n--- Uploaded Evidence Files (MongoDB) ---")
        for i, ev in enumerate(evidence_list, 1):
            filename = ev.get("filename") or ev.get("original_filename") or "Unknown"
            file_type = ev.get("file_type") or ev.get("parser_type") or "raw"
            status = ev.get("status", "unknown")
            raw_b = ev.get("size_bytes") or ev.get("file_size_bytes") or ev.get("file_size") or 0
            size_kb = raw_b / 1024
            lines.append(f"{i}. {filename} (Type: {file_type}, Status: {status}, Size: {size_kb:.1f} KB)")

    # Semantic search results (FAISS vector store)
    if semantic_context:
        lines.append("\n--- Relevant Evidence Events (FAISS Vector Search Matches) ---")
        for i, sc in enumerate(semantic_context[:8], 1):
            lines.append(
                f"{i}. [{sc.get('severity')}] {sc.get('timestamp')} | "
                f"{sc.get('subject')} → {sc.get('action')} → {sc.get('object')} "
                f"(source: {sc.get('evidence_file', 'log')})"
            )

    # Timeline sessions (timeline intent)
    if timeline_ctx and timeline_ctx.get("sessions"):
        lines.append(
            f"\n--- Timeline: {timeline_ctx['total']} events across "
            f"{len(timeline_ctx['sessions'])} activity sessions "
            f"(span: {timeline_ctx['span_hours']}h) ---"
        )
        for s in timeline_ctx["sessions"][:5]:
            lines.append(
                f"  Session: {s.get('count')} events "
                f"from {s.get('start')} to {s.get('end')}"
            )

    # Top anomalies
    lines.append("\n--- Top ML Anomalies (Isolation Forest Model) ---")
    if anomalies:
        for i, a in enumerate(anomalies[:12], 1):
            mitre = ", ".join(a.get("mitre_techniques", [])) or "none"
            lines.append(
                f"{i}. [{a.get('severity').upper()}] {a.get('timestamp')} | "
                f"{a.get('subject')} → {a.get('action')} → {a.get('object')} | "
                f"score={a.get('anomaly_score', 0):.4f} | MITRE: {mitre}"
            )
    else:
        lines.append("  No anomalies detected yet.")

    # Graph correlations
    if correlations:
        lines.append(f"\n--- Neo4j Graph Correlations ({len(correlations)} derived relationships) ---")
        for c in correlations[:10]:
            mitre = f" | MITRE {c['mitre']} ({c.get('technique','')})" if c.get("mitre") else ""
            lines.append(
                f"  [{c.get('rule')}] {c.get('source')} → {c.get('target')}{mitre}"
            )

    # MITRE techniques
    if enriched_techniques:
        lines.append("\n--- Observed MITRE ATT&CK Techniques ---")
        for t in enriched_techniques:
            lines.append(f"  {t['id']} [{t['tactic']}]: {t['name']}")

    q_lower = (question or "").strip().lower()
    is_greeting = q_lower in ["hi", "hii", "hy", "hye", "hello", "helo", "hey", "yo", "sup", "greetings"]

    if is_greeting:
        lines.append(
            f"\nInvestigator Question: \"{question}\"\n"
            f"SPECIAL GREETING INSTRUCTION: Respond warmly and professionally as follows:\n"
            f"\"Hello! I am ForenSight, your AI forensic investigator assistant. I have loaded and analyzed the case logs for {case.get('title')}.\"\n"
            f"Provide a quick 1-2 sentence overview of the loaded dataset ({len(evidence_list)} evidence files, {len(anomalies)} anomalies), "
            f"and invite the investigator to ask ANY specific questions about evidence files, processes, IPs, or timelines."
        )
    elif question:
        lines.append(
            f"\nInvestigator Question: \"{question}\"\n"
            "SYSTEM INSTRUCTION FOR COPILOT:\n"
            "You are ForenSight AI Copilot, an expert digital forensics assistant. Answer ANY custom question asked by the investigator using the complete project database context provided above (MongoDB evidence files & events, Neo4j graph correlations, Isolation Forest ML anomalies, and FAISS vector matches).\n"
            "1. Deliver clear, intelligent, natural paragraph-wise explanations (ChatGPT/Gemini style).\n"
            "2. Cite exact evidence file names, process names, IP addresses, timestamps, or command lines from the database context when relevant.\n"
            "3. If the user asks about a specific file, IP, process, or event, filter the context to answer that exact question.\n"
            "4. If the question asks about something not present in the logs, state that clearly and suggest what evidence to inspect next.\n"
            "Output ONLY your final answer in clean, professional Markdown. Do NOT include system constraints, roles, or prompt text in your output."
        )
    else:
        lines.append(
            "\nWrite a concise forensic analysis report in Markdown. "
            "Highlight key attack patterns, suspicious entities, and recommend concrete containment steps."
        )

    return "\n".join(lines)


class CopilotService:

    @classmethod
    async def analyze_case_timeline(
        cls, case_id: str, org_id: str, question: Optional[str] = None, history: Optional[List[dict]] = None
    ) -> Any:
        """
        Main entry point — routes queries, builds fenced context, selects LLM provider, and returns structured analysis + sources.
        """
        intent = classify_intent(question or "")
        logger.info(f"Copilot analysis: case={case_id} intent={intent}")

        # 1. Fast Path: Structured DB Queries (Counts, Status, Evidence List, File Security)
        structured_res = await handle_structured_query(case_id, org_id, question or "", intent, history=history)
        if structured_res:
            return structured_res

        # 2. Assemble RAG Context (MongoDB, PyOD, Neo4j, FAISS)
        ctx = await build_copilot_context(case_id, org_id, question)
        if not ctx:
            return {"analysis": "Case not found or access denied.", "confidence": "Low", "sources": []}
        ctx["history"] = history or []

        # 3. Build Fenced Prompt (Prompt-Injection Safe)
        from backend.app.services.copilot.prompts import build_fenced_prompt
        prompt = build_fenced_prompt(ctx)

        # Build default source citations from context
        sources = []
        for ev in ctx.get("evidence_list", []):
            sources.append({"type": "evidence_file", "source_file": ev.get("filename", "evidence"), "status": ev.get("status", "parsed")})
        for sc in ctx.get("semantic_context", [])[:3]:
            sources.append({"type": "event_log", "source_file": sc.get("evidence_file", "log"), "event_id": str(sc.get("_id", ""))})
        for tech in ctx.get("enriched_techniques", [])[:3]:
            sources.append({"type": "mitre_technique", "mitre_id": tech.get("id"), "name": tech.get("name")})

        # 4. LLM Generation
        provider_name = os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER).lower()
        analysis_text = ""

        if provider_name == "local":
            analysis_text = _local_fallback(ctx)
        elif provider_name == "ollama":
            try:
                from backend.app.services.copilot.ollama_provider import OllamaProvider
                analysis_text = await OllamaProvider().generate(prompt)
            except Exception as e:
                logger.warning(f"Ollama failed ({e}), falling back to local.")
                analysis_text = _local_fallback(ctx)
        else:
            api_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY)
            if not api_key:
                analysis_text = _local_fallback(ctx)
            else:
                try:
                    from backend.app.services.copilot.gemini_provider import GeminiProvider
                    analysis_text = await GeminiProvider(api_key=api_key).generate(prompt)
                except Exception as e:
                    logger.warning(f"Gemini API rate limited ({e}), seamlessly serving from local forensic engine.")
                    analysis_text = _local_fallback(ctx)

        # 5. Parse JSON if LLM returned structured JSON
        import json
        if analysis_text and "{" in analysis_text and "}" in analysis_text:
            try:
                # Extract JSON payload if surrounded by markdown code blocks
                j_str = analysis_text
                if "```json" in j_str:
                    j_str = j_str.split("```json")[1].split("```")[0].strip()
                elif "```" in j_str:
                    j_str = j_str.split("```")[1].split("```")[0].strip()
                parsed = json.loads(j_str.strip())
                if isinstance(parsed, dict) and "analysis" in parsed:
                    return {
                        "analysis": parsed.get("analysis", analysis_text),
                        "confidence": parsed.get("confidence", "High"),
                        "sources": parsed.get("sources", sources) or sources
                    }
            except Exception:
                pass

        return {
            "analysis": analysis_text,
            "confidence": "High" if len(sources) > 0 else "Medium",
            "sources": sources
        }


def _local_fallback(ctx: dict) -> str:
    """Use the local report generator when no LLM API is available."""
    return build_forensic_report(
        case=ctx["case"],
        anomalies=ctx["anomalies"],
        correlations=ctx["correlations"],
        enriched_techniques=ctx["enriched_techniques"],
        semantic_context=ctx["semantic_context"],
        evidence_list=ctx.get("evidence_list"),
        question=ctx.get("question"),
    )
