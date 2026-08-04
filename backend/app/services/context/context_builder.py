"""
Context Builder — ForenSight AI  (master assembler)
======================================================
Single entry point that wires all sub-builders together and returns the
fully assembled context dict for the copilot or report generator.

Architecture Section 5.6.1:
  intent → retrieval tool → context → LLM → answer with citations
"""

import logging
from typing import Any, Dict, List, Optional

from backend.app.repositories.case_repository import CaseRepository
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.services.ai.vector_store import VectorStore
from backend.app.services.context.anomaly_context import build_anomaly_context
from backend.app.services.context.graph_context import build_graph_context
from backend.app.services.context.timeline_context import build_timeline_context
from backend.app.knowledge.mitre_mapper import MitreMapper
from backend.app.services.copilot.question_router import classify_intent, Intent

logger = logging.getLogger(__name__)


async def build_copilot_context(
    case_id: str,
    org_id: str,
    question: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Assemble a full context package for the copilot prompt.

    Routing:
      - similarity intent  → FAISS vector search results
      - timeline intent    → chronological session grouping
      - factual / summarise → anomalies + graph correlations + evidence list

    Returns a dict with keys:
      case, intent, anomalies, correlations, enriched_techniques,
      semantic_context, timeline_ctx, evidence_list, question
    """
    case = await CaseRepository.get_by_id(case_id, org_id)
    if not case:
        return {}

    intent: Intent = classify_intent(question or "")
    logger.info(f"[ContextBuilder] intent='{intent}' for case {case_id}")

    # Fetch anomalies, graph correlations, and evidence list
    import asyncio
    anomalies, correlations, evidence_list = await asyncio.gather(
        build_anomaly_context(case, limit=30),
        build_graph_context(case_id, org_id),
        EvidenceRepository.list_by_case(case_id, org_id),
    )

    # Intent-specific retrieval
    semantic_context: List[Dict[str, Any]] = []
    timeline_ctx: Dict[str, Any] = {}

    if intent == "similarity" and question:
        semantic_context = await VectorStore.search_similar_events(
            case_id, org_id, query=question, limit=8
        )

    elif intent == "timeline":
        timeline_ctx = await build_timeline_context(case, limit=200)

    else:
        # For factual + summarise, also run similarity if there's a question
        if question:
            semantic_context = await VectorStore.search_similar_events(
                case_id, org_id, query=question, limit=5
            )

    # Collect + enrich MITRE techniques
    technique_ids: set = set()
    for a in anomalies:
        for t in a.get("mitre_techniques", []):
            technique_ids.add(t)
    for c in correlations:
        if c.get("mitre"):
            technique_ids.add(c["mitre"])
    enriched_techniques = MitreMapper.enrich_techniques(list(technique_ids))

    return {
        "case": case,
        "intent": intent,
        "question": question,
        "anomalies": anomalies,
        "correlations": correlations,
        "enriched_techniques": enriched_techniques,
        "semantic_context": semantic_context,
        "timeline_ctx": timeline_ctx,
        "evidence_list": evidence_list,
    }
