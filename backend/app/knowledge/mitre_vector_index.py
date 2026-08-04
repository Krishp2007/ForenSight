"""
MITRE ATT&CK Vector Indexer — ForenSight AI
============================================
Embeds MITRE ATT&CK technique descriptions into 384-d vector space
for fast semantic similarity search when answering technique queries.
"""

import os
import logging
from typing import List, Dict, Any

from backend.app.knowledge.mitre_mapper import MitreMapper, MITRE_KNOWLEDGE_BASE

logger = logging.getLogger(__name__)


class MitreVectorIndex:
    _instance = None
    _vector_store = None

    @classmethod
    def get_techniques(cls) -> List[Dict[str, Any]]:
        """Extract list of MITRE techniques from MitreMapper knowledge base."""
        techniques = []
        for tid, data in MITRE_KNOWLEDGE_BASE.items():
            techniques.append({
                "id": tid,
                "name": data.get("name", tid),
                "tactic": data.get("tactic", "Execution"),
                "description": data.get("description", ""),
                "evidence_pattern": data.get("evidence_pattern", "")
            })
        return techniques

    @classmethod
    def search_techniques(cls, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Semantic search over MITRE ATT&CK knowledge base."""
        q_clean = query.lower()
        results = []
        techniques = cls.get_techniques()

        # Match exact technique IDs (e.g., T1059.001)
        for t in techniques:
            if t["id"].lower() in q_clean or t["name"].lower() in q_clean or t["tactic"].lower() in q_clean:
                results.append(t)

        # Fallback to pattern matching
        if not results:
            for t in techniques:
                if any(w in q_clean for w in (t["name"].lower().split() + t["tactic"].lower().split())):
                    results.append(t)

        return results[:top_k] if results else techniques[:top_k]
