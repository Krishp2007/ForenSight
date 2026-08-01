"""
Question Router — ForenSight AI
==================================
Classifies the investigator's intent into one of four categories
(architecture Section 5.6.1) and routes to the correct retrieval tool.

Intent categories:
  factual      → direct Cypher graph lookup
  timeline     → chronological event range query
  similarity   → FAISS vector search
  summarise    → full case summary (default)

Classification is rule-based (no ML needed for a small keyword set),
keeping the system fast and deterministic.
"""

from typing import Literal

Intent = Literal["factual", "timeline", "similarity", "summarise"]

# Keyword sets for each intent bucket
_TIMELINE_KEYS = {
    "timeline", "sequence", "when", "order", "chronolog", "before", "after",
    "history", "chain", "first", "last", "earliest", "latest",
}

_FACTUAL_KEYS = {
    "what", "which", "who", "where", "show me", "list", "find", "get",
    "tell me about", "explain", "describe", "detail",
}

_SIMILARITY_KEYS = {
    "similar", "like", "match", "related", "previous", "past case",
    "compare", "remind", "seen before", "same technique",
}

_SUMMARISE_KEYS = {
    "summary", "summarise", "summarize", "overview", "report",
    "analyse", "analyze", "investigate", "audit", "assess",
}


def classify_intent(question: str) -> Intent:
    """
    Map a free-text investigator question to one of four intent labels.

    Precedence (highest → lowest):
      similarity > timeline > factual > summarise

    Returns 'summarise' when no keywords match (safe default).
    """
    if not question:
        return "summarise"

    q = question.lower()

    if any(k in q for k in _SIMILARITY_KEYS):
        return "similarity"

    if any(k in q for k in _TIMELINE_KEYS):
        return "timeline"

    if any(k in q for k in _FACTUAL_KEYS):
        return "factual"

    if any(k in q for k in _SUMMARISE_KEYS):
        return "summarise"

    # Default — ask for a full case summary
    return "summarise"
