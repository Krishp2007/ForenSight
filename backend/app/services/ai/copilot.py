"""
Copilot Service — ForenSight AI  (v2 — Groq Primary + Fallback)
=================================================================
Orchestrates the full RAG pipeline:
  1. Intent routing (fast-path structured DB queries)
  2. Build context via ContextBuilder (FAISS + Neo4j + MongoDB)
  3. Try Groq API (primary) — streaming + non-streaming
  4. On any Groq failure → fall back to local forensic report engine (same context)
  5. Return markdown response with citations

Fallback triggers:
  - API timeout / connection error
  - Auth failure (401/403)
  - Rate limit (429)
  - Server error (5xx)
  - Empty or insufficient response ("I don't know" etc.)
  - Any unexpected exception

Internal logging only — never exposed to the frontend.
"""

import asyncio
import logging
import os
from typing import Any, AsyncGenerator, List, Optional

from backend.app.config import settings
from backend.app.services.context.context_builder import build_copilot_context
from backend.app.services.copilot.query_router import classify_intent, handle_structured_query
from backend.app.services.copilot.report_generator import build_forensic_report
from backend.app.services.copilot.prompts import build_fenced_prompt, SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Configuration defaults (can be overridden via env vars)
MAX_HISTORY_TURNS = int(os.getenv("COPILOT_MAX_HISTORY_TURNS", "5"))  # keep last N user‑assistant pairs
GROQ_TOKENS_PER_MIN = int(os.getenv("GROQ_TOKENS_PER_MIN", "20000"))  # default token budget per minute

# Token‑bucket limiter for Groq usage
from .token_limiter import TokenBucket
groq_token_bucket = TokenBucket(max_tokens_per_minute=GROQ_TOKENS_PER_MIN)

from backend.app.services.copilot.groq_provider import _is_insufficient


# ── Source citation builder ───────────────────────────────────────────────────
def _build_sources(ctx: dict) -> list:
    sources = []
    for ev in ctx.get("evidence_list", []):
        fn = ev.get("filename") or ev.get("original_filename") or "evidence"
        eid = str(ev.get("_id", "") or ev.get("id", ""))
        sources.append({
            "type": "evidence_file",
            "source_file": fn,
            "evidence_id": eid,
            "status": ev.get("status", "parsed"),
        })
    for sc in ctx.get("semantic_context", [])[:4]:
        sources.append({
            "type": "event_log",
            "source_file": sc.get("evidence_file", "log"),
            "event_id": str(sc.get("_id", "")),
            "event_type": sc.get("event_type", ""),
            "timestamp": str(sc.get("timestamp", "")),
        })
    for tech in ctx.get("enriched_techniques", [])[:3]:
        sources.append({
            "type": "mitre_technique",
            "mitre_id": tech.get("id"),
            "name": tech.get("name"),
            "tactic": tech.get("tactic", ""),
        })
    for corr in ctx.get("correlations", [])[:2]:
        if corr.get("mitre"):
            sources.append({
                "type": "graph_correlation",
                "source_file": "Neo4j Graph",
                "mitre_id": corr.get("mitre"),
                "rule": corr.get("rule", ""),
            })
    return sources


# ── Prompt splitter for Groq (system + user) ─────────────────────────────────
def _split_prompt(ctx: dict) -> tuple[str, str]:
    """Split build_fenced_prompt output into system + user messages for Groq."""
    full_prompt = build_fenced_prompt(ctx)
    # Everything up to INVESTIGATOR QUESTION is the system context
    marker = "================ INVESTIGATOR QUESTION ================"
    if marker in full_prompt:
        parts = full_prompt.split(marker, 1)
        system_part = parts[0].strip()
        user_part = (marker + parts[1]).strip()
    else:
        system_part = SYSTEM_PROMPT
        user_part = full_prompt
    return system_part, user_part


# ── Fallback text generation ──────────────────────────────────────────────────
async def _run_fallback(ctx: dict, prompt: str) -> str:
    """Groq failed — fall back directly to the local deterministic report engine."""
    logger.info("[Copilot] Fallback: Using local forensic report engine")
    return build_forensic_report(
        case=ctx["case"],
        anomalies=ctx["anomalies"],
        correlations=ctx["correlations"],
        enriched_techniques=ctx["enriched_techniques"],
        semantic_context=ctx["semantic_context"],
        evidence_list=ctx.get("evidence_list"),
        question=ctx.get("question"),
    )


# ── Main CopilotService ───────────────────────────────────────────────────────
import re as _re
_FILENAME_RE = _re.compile(r'\b[\w\-. ]+\.(sqlite|pcap|pcapng|csv|json|log|txt|zip)\b', _re.IGNORECASE)


def _extract_mentioned_filenames(text: str) -> set:
    """Return the set of evidence filenames mentioned in a piece of text."""
    if not text:
        return set()
    return {m.group(0) for m in _FILENAME_RE.finditer(text)}


class CopilotService:

    @classmethod
    async def analyze_case_timeline(
        cls,
        case_id: str,
        org_id: str,
        question: Optional[str] = None,
        history: Optional[List[dict]] = None,
    ) -> Any:
        """
        Non-streaming entry point (backward compatible).
        Returns dict with analysis, confidence, sources.
        """
        intent = classify_intent(question or "")
        logger.info(f"[Copilot] case={case_id} intent={intent}")

        # Fast-path: structured DB queries (counts, file list, status, etc.)
        structured_res = await handle_structured_query(
            case_id, org_id, question or "", intent, history=history
        )
        if structured_res:
            return structured_res

        # Build full RAG context
        ctx = await build_copilot_context(case_id, org_id, question)
        if not ctx:
            return {"analysis": "Case not found or access denied.", "confidence": "Low", "sources": []}

        ctx["history"] = history or []
        sources = _build_sources(ctx)

        # Sanitize history to remove assistant turns referencing deleted evidence
        current_filenames = {ev.get("filename", "") for ev in ctx.get("evidence_list", [])}
        sanitized_history = []
        for turn in (history or []):
            if turn.get("role") == "assistant":
                content = turn.get("content", "")
                if any(
                    fn and fn in content
                    for fn in (_extract_mentioned_filenames(content) - current_filenames)
                ):
                    continue
            sanitized_history.append(turn)
        # Trim history to the most recent N turns (user + assistant = 2 * N entries)
        if len(sanitized_history) > MAX_HISTORY_TURNS * 2:
            sanitized_history = sanitized_history[-MAX_HISTORY_TURNS * 2:]
        ctx["history"] = sanitized_history

        # Build prompt
        full_prompt = build_fenced_prompt(ctx)
        system_prompt, user_prompt = _split_prompt(ctx)

        # Try Groq first
        ai_provider = os.getenv("AI_PROVIDER", getattr(settings, "AI_PROVIDER", "groq")).lower()
        enable_fallback = os.getenv("ENABLE_FALLBACK", "true").lower() in ("true", "1", "yes")
        analysis_text = ""

        if ai_provider == "groq":
            groq_key = os.getenv("GROQ_API_KEY", getattr(settings, "GROQ_API_KEY", ""))
            if groq_key and groq_key not in ("", "your_groq_api_key_here"):
                try:
                    logger.info("[Copilot] Using Groq provider")
                    from backend.app.services.copilot.groq_provider import GroqProvider, GroqError
                    analysis_text = await GroqProvider().generate(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        history=history or [],
                    )
                    logger.info("[Copilot] Groq responded successfully")
                except Exception as e:
                    if enable_fallback:
                        logger.warning(f"[Copilot] Groq failed ({type(e).__name__}: {e}), switching to fallback")
                        analysis_text = await _run_fallback(ctx, full_prompt)
                    else:
                        logger.error(f"[Copilot] Groq failed and fallback disabled: {e}")
                        return {
                            "analysis": "Sorry, I couldn't generate a response at this time. Please try again.",
                            "confidence": "Low",
                            "sources": [],
                        }
            else:
                logger.warning("[Copilot] Groq API key not set, using fallback directly")
                analysis_text = await _run_fallback(ctx, full_prompt)
        else:
            # Non-Groq provider path (legacy)
            analysis_text = await _run_fallback(ctx, full_prompt)

        if not analysis_text:
            logger.error("[Copilot] Both providers failed — returning error message")
            return {
                "analysis": "Sorry, I couldn't generate a response at this time. Please try again.",
                "confidence": "Low",
                "sources": [],
            }

        return {
            "analysis": analysis_text,
            "confidence": "High" if sources else "Medium",
            "sources": sources,
        }

    @classmethod
    async def stream_response(
        cls,
        case_id: str,
        org_id: str,
        question: str,
        history: Optional[List[dict]] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        SSE streaming entry point.
        Yields dicts: {type: "token"|"sources"|"done"|"error", content/sources/confidence}

        Groq is instructed to return plain Markdown analysis only (no JSON).
        We buffer the full response then stream it word-by-word for the typewriter effect.
        """

        intent = classify_intent(question)
        logger.info(f"[Copilot Stream] case={case_id} intent={intent}")

        # ── Fast-path: structured DB queries ──────────────────────────────────
        structured_res = await handle_structured_query(
            case_id, org_id, question, intent, history=history
        )
        if structured_res:
            text = structured_res.get("analysis", "")
            words = text.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield {"type": "token", "content": chunk}
                if i % 10 == 0:
                    await asyncio.sleep(0)
            yield {"type": "sources", "sources": structured_res.get("sources", [])}
            yield {"type": "done", "confidence": structured_res.get("confidence", "High")}
            return

        # ── Build RAG context ─────────────────────────────────────────────────
        ctx = await build_copilot_context(case_id, org_id, question)
        if not ctx:
            yield {"type": "error", "content": "Case not found or access denied."}
            return

        ctx["history"] = history or []
        sources = _build_sources(ctx)

        # Sanitize history: remove assistant turns that reference evidence
        # filenames no longer in this case. This prevents the LLM from
        # hallucinating answers based on deleted evidence it saw in prior turns.
        current_filenames = {
            ev.get("filename", "") for ev in ctx.get("evidence_list", [])
        }
        sanitized_history = []
        for turn in (history or []):
            if turn.get("role") == "assistant":
                content = turn.get("content", "")
                # Drop this assistant turn if it mentions a filename that no longer
                # exists in the case — it means it was about deleted evidence.
                if any(
                    fn and fn in content
                    for fn in (
                        # Extract only names that were deleted (not in current list)
                        _extract_mentioned_filenames(content) - current_filenames
                    )
                ):
                    continue  # skip stale turn
            sanitized_history.append(turn)
        # Apply the same history‑length limit as the non‑streaming path
        if len(sanitized_history) > MAX_HISTORY_TURNS * 2:
            sanitized_history = sanitized_history[-MAX_HISTORY_TURNS * 2:]
        ctx["history"] = sanitized_history

        system_prompt, user_prompt = _split_prompt(ctx)
        full_prompt = build_fenced_prompt(ctx)

        ai_provider = os.getenv("AI_PROVIDER", getattr(settings, "AI_PROVIDER", "groq")).lower()
        enable_fallback = os.getenv("ENABLE_FALLBACK", "true").lower() in ("true", "1", "yes")
        groq_key = os.getenv("GROQ_API_KEY", getattr(settings, "GROQ_API_KEY", ""))
        groq_available = (
            ai_provider == "groq"
            and bool(groq_key)
            and groq_key not in ("", "your_groq_api_key_here")
        )
        # Estimate token usage for this request and enforce the bucket limit
        estimated_tokens = len((system_prompt + " " + user_prompt).split())
        if not groq_token_bucket.consume(estimated_tokens):
            logger.warning("[Copilot Stream] Token bucket exhausted – falling back to local engine")
            groq_available = False

        # ── Groq primary path ─────────────────────────────────────────────────
        if groq_available:
            try:
                logger.info("[Copilot Stream] Using Groq streaming provider")
                from backend.app.services.copilot.groq_provider import GroqProvider

                provider = GroqProvider()

                # Buffer the full Groq response — we must NOT stream raw JSON tokens.
                full_text = ""
                async for chunk in provider.generate_stream(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    history=history or [],
                ):
                    full_text += chunk

                logger.info("[Copilot Stream] Groq stream completed successfully")

                # Stream the plain Markdown response word-by-word (typewriter effect)
                words = full_text.split(" ")
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    yield {"type": "token", "content": chunk}
                    if i % 12 == 0:
                        await asyncio.sleep(0)

                yield {"type": "sources", "sources": sources}
                yield {"type": "done", "confidence": "High" if sources else "Medium"}
                return

            except Exception as e:
                if enable_fallback:
                    logger.warning(
                        f"[Copilot Stream] Groq failed ({type(e).__name__}: {e}), switching to fallback"
                    )
                else:
                    logger.error(f"[Copilot Stream] Groq failed and fallback disabled: {e}")
                    yield {"type": "error", "content": "Sorry, I couldn't generate a response at this time. Please try again."}
                    return

        # ── Fallback path (no Groq key, or Groq raised + fallback enabled) ────
        try:
            logger.info("[Copilot Stream] Running fallback provider")
            fallback_text = await _run_fallback(ctx, full_prompt)
            if fallback_text:
                words = fallback_text.split(" ")
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    yield {"type": "token", "content": chunk}
                    if i % 8 == 0:
                        await asyncio.sleep(0)
            else:
                logger.error("[Copilot Stream] Fallback returned empty response")
                yield {"type": "error", "content": "Sorry, I couldn't generate a response at this time. Please try again."}
                return
        except Exception as e:
            logger.error(f"[Copilot Stream] Fallback failed: {e}")
            yield {"type": "error", "content": "Sorry, I couldn't generate a response at this time. Please try again."}
            return

        yield {"type": "sources", "sources": sources}
        yield {"type": "done", "confidence": "High" if sources else "Medium"}


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
