"""
Cross-Case Similarity Service — ForenSight AI
================================================
Architecture Section 5.5.3:
  "Every case produces a set of artefact summaries… embedded and indexed
   in Qdrant. When a new case is loaded, the reasoning layer queries the
   index to surface the top-K most similar prior cases."

This service:
  1. Generates a case summary embedding using BGE
  2. Upserts it into the shared Qdrant 'cases' collection
  3. Queries for the K nearest neighbours across ALL cases
     (not just the current one — this is the cross-case difference from FAISS)
"""

import logging
import hashlib
from typing import Any, Dict, List, Optional

from backend.app.services.intelligence.embeddings.bge import BGEEmbedder
from backend.app.db.mongodb import db_client

logger = logging.getLogger(__name__)

_embedder = BGEEmbedder()
COLLECTION = "case_similarity_index"   # Qdrant collection name


def _case_to_text(case: Dict[str, Any], anomalies: List[Dict]) -> str:
    """
    Build a short structured description of the case's observed techniques
    and key entities for embedding.
    """
    lines = [
        f"Case: {case.get('title', 'Untitled')}",
        f"Status: {case.get('status', 'open')}",
    ]
    if case.get("description"):
        lines.append(f"Description: {case['description']}")

    techniques = set()
    subjects = set()
    for a in anomalies[:20]:
        for t in a.get("mitre_techniques", []):
            techniques.add(t)
        subjects.add(a.get("subject", ""))

    if techniques:
        lines.append(f"MITRE techniques observed: {', '.join(sorted(techniques))}")
    if subjects:
        lines.append(f"Key entities: {', '.join(list(subjects)[:10])}")

    return " | ".join(lines)


async def index_case_for_similarity(
    case_id: str, org_id: str
) -> bool:
    """
    Embed the case summary and upsert into Qdrant for cross-case search.
    Called at the end of the processing pipeline.
    """
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct, VectorParams, Distance
        from backend.app.config import settings
    except ImportError:
        logger.warning("qdrant-client not installed — skipping cross-case indexing.")
        return False

    from backend.app.repositories.case_repository import CaseRepository
    from backend.app.db.mongodb import db_client as mdb

    case = await CaseRepository.get_by_id(case_id, org_id)
    if not case:
        return False

    # Fetch anomaly sample for text generation
    cursor = mdb.db["events"].find(
        {"case_id": case["_id"], "is_anomaly": True}
    ).sort("anomaly_score", -1).limit(20)
    anomalies = await cursor.to_list(20)

    text = _case_to_text(case, anomalies)
    vec = _embedder.encode([text], is_query=False)[0].tolist()

    # Stable integer ID from case_id hash
    point_id = int(hashlib.md5(case_id.encode()).hexdigest()[:8], 16)

    try:
        from backend.app.config import settings
        client = QdrantClient(host="qdrant", port=6333, timeout=5)

        # Create collection if needed
        existing = [c.name for c in client.get_collections().collections]
        if COLLECTION not in existing:
            client.create_collection(
                COLLECTION,
                vectors_config=VectorParams(
                    size=_embedder.dimension, distance=Distance.COSINE
                ),
            )

        client.upsert(
            collection_name=COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vec,
                    payload={
                        "case_id": case_id,
                        "org_id": org_id,
                        "title": case.get("title", ""),
                        "status": case.get("status", ""),
                        "summary_text": text[:500],
                    },
                )
            ],
        )
        logger.info(f"[Similarity] Case {case_id} indexed in Qdrant.")
        return True
    except Exception as e:
        logger.warning(f"[Similarity] Qdrant upsert failed: {e}")
        return False


async def find_similar_cases(
    case_id: str, org_id: str, top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Query Qdrant for the top-K most similar prior cases.
    Excludes the current case from results.

    Returns list of { case_id, title, score, summary_text }
    """
    try:
        from qdrant_client import QdrantClient
        from backend.app.config import settings
    except ImportError:
        return []

    from backend.app.repositories.case_repository import CaseRepository
    from backend.app.db.mongodb import db_client as mdb

    case = await CaseRepository.get_by_id(case_id, org_id)
    if not case:
        return []

    cursor = mdb.db["events"].find(
        {"case_id": case["_id"], "is_anomaly": True}
    ).limit(20)
    anomalies = await cursor.to_list(20)

    text = _case_to_text(case, anomalies)
    vec = _embedder.encode([text], is_query=True)[0].tolist()

    try:
        client = QdrantClient(host="qdrant", port=6333, timeout=5)
        hits = client.search(
            collection_name=COLLECTION,
            query_vector=vec,
            limit=top_k + 1,   # +1 to account for self
            with_payload=True,
        )
        results = []
        for h in hits:
            if h.payload.get("case_id") == case_id:
                continue   # skip self
            results.append(
                {
                    "case_id": h.payload["case_id"],
                    "title": h.payload.get("title", ""),
                    "score": round(h.score, 4),
                    "summary_text": h.payload.get("summary_text", ""),
                }
            )
        return results[:top_k]
    except Exception as e:
        logger.warning(f"[Similarity] Qdrant search failed: {e}")
        return []
