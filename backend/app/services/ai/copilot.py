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
from typing import Optional

from backend.app.config import settings
from backend.app.services.context.context_builder import build_copilot_context
from backend.app.services.copilot.question_router import classify_intent
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
        "You are ForenSight, a digital forensics assistant.",
        "You answer questions about the active investigation case only.",
        "Every claim you make must cite at least one event, entity, or technique ID "
        "from the supplied context. If the context does not contain enough information "
        "to answer, say so explicitly.",
        "Format timestamps in UTC ISO-8601.",
        "When suggesting next steps, suggest concrete graph queries or parsers to run.",
        "",
        f"Case Title: {case.get('title')}",
        f"Case Description: {case.get('description', 'N/A')}",
        f"Case Status: {case.get('status', 'open')}",
        f"Intent classified as: {intent}",
    ]

    if question:
        lines.append(f"\nInvestigator question: \"{question}\"")

    # Semantic search results (similarity / factual with question)
    if semantic_context:
        lines.append("\n--- Semantically similar events (FAISS) ---")
        for i, sc in enumerate(semantic_context[:6], 1):
            lines.append(
                f"{i}. [{sc.get('severity')}] {sc.get('timestamp')} | "
                f"{sc.get('subject')} → {sc.get('action')} → {sc.get('object')} "
                f"(distance: {sc.get('distance', 0):.4f})"
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
    lines.append("\n--- Top ML Anomalies (Isolation Forest) ---")
    if anomalies:
        for i, a in enumerate(anomalies[:10], 1):
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
        lines.append(f"\n--- Graph Correlation Rules ({len(correlations)} derived) ---")
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

    lines.append(
        "\nWrite a professional forensic analysis report in Markdown. "
        "Highlight attack patterns, suspicious entities, and recommend "
        "concrete containment steps. Cite evidence IDs or entity names inline."
    )

    return "\n".join(lines)


class CopilotService:

    @classmethod
    async def analyze_case_timeline(
        cls, case_id: str, org_id: str, question: Optional[str] = None
    ) -> str:
        """
        Main entry point — builds context, selects provider, returns Markdown.
        """
        logger.info(f"Copilot analysis: case={case_id} intent={classify_intent(question or '')}")

        # 1. Assemble full context
        ctx = await build_copilot_context(case_id, org_id, question)
        if not ctx:
            return "Case not found or access denied."

        # 2. Build prompt
        prompt = _build_prompt(ctx)

        # 3. Select provider + generate
        provider_name = os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER).lower()

        if provider_name == "local":
            return _local_fallback(ctx)

        if provider_name == "ollama":
            try:
                from backend.app.services.copilot.ollama_provider import OllamaProvider
                return await OllamaProvider().generate(prompt)
            except Exception as e:
                logger.warning(f"Ollama failed ({e}), falling back to local.")
                return _local_fallback(ctx)

        # Default: Gemini
        api_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY)
        if not api_key:
            return _local_fallback(ctx)

        try:
            from backend.app.services.copilot.gemini_provider import GeminiProvider
            return await GeminiProvider(api_key=api_key).generate(prompt)
        except Exception as e:
            logger.warning(f"Gemini failed ({e}), falling back to local.")
            return _local_fallback(ctx)


def _local_fallback(ctx: dict) -> str:
    """Use the local report generator when no LLM API is available."""
    return build_forensic_report(
        case=ctx["case"],
        anomalies=ctx["anomalies"],
        correlations=ctx["correlations"],
        enriched_techniques=ctx["enriched_techniques"],
        semantic_context=ctx["semantic_context"],
        question=ctx.get("question"),
    )
