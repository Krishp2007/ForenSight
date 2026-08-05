import os
import pickle
import hashlib
import logging
import time
import numpy as np
from typing import List, Dict, Any

# Suppress harmless HuggingFace hub rate limit/symlinks warning logs
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from bson import ObjectId

from backend.app.db.mongodb import db_client
from backend.app.config import settings

logger = logging.getLogger(__name__)

# Initialize sentence transformer model lazily to avoid loading times on import
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        import torch
        torch.set_num_threads(1)
        torch.set_grad_enabled(False)
        from sentence_transformers import SentenceTransformer
        logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2' (1 CPU thread, grad off)...")
        cache_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".cache")
        _model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=cache_folder)
    return _model


class VectorStore:
    @staticmethod
    def get_index_paths(case_id: str):
        """Get local directory and file paths for the case's FAISS index."""
        base_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "storage", "vector_indexes", case_id
        )
        os.makedirs(base_dir, exist_ok=True)
        return {
            "index": os.path.join(base_dir, "index.faiss"),
            "meta":  os.path.join(base_dir, "metadata.pkl")
        }

    @classmethod
    def format_event_sentence(cls, event: Dict[str, Any]) -> str:
        """
        Translate a CFM event record into a clear natural language statement.
        For browser history, uses domain-level normalization to reduce duplicates.
        """
        source = str(event.get("source", "")).lower()

        if source == "browser":
            # For browser events: normalize to domain + action + severity
            # This means repeated visits to google.com produce the same sentence → deduplicated
            details = event.get("details", {}) or {}
            obj = event.get("object", "")
            # Extract domain for normalization
            try:
                from urllib.parse import urlparse
                if not obj.startswith(("http://", "https://")):
                    obj_parsed = "http://" + obj
                else:
                    obj_parsed = obj
                domain = urlparse(obj_parsed).hostname or obj
                domain = domain.lstrip("www.")
            except Exception:
                domain = obj
            act = event.get("action", "visited")
            sev = event.get("severity", "info")
            return f"Browser '{act}' domain '{domain}'. Threat Severity: {sev}."
        else:
            # Non-browser: full sentence with timestamp (preserves all unique events)
            ts = event.get("timestamp")
            ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
            subj = event.get("subject", "unknown subject")
            act = event.get("action", "performed action")
            obj = event.get("object", "unknown target")
            sev = event.get("severity", "info")
            return f"At {ts_str}, {subj} performed '{act}' on '{obj}'. Threat Severity: {sev}."

    @classmethod
    async def index_case_events(cls, case_id: str, org_id: str) -> bool:
        """
        Load events for a case, deduplicate semantic content, generate embeddings,
        and build the FAISS index. Separate profiling for each stage.

        Key optimizations:
        1. Deduplication: identical sentences → one embedding (safe for browser history)
        2. All event IDs preserved in metadata mapped to their deduplicated embedding
        3. No arbitrary event cap — uses deduplication to bound embedding count
        """
        _t_total = time.perf_counter()
        logger.info(f"[FAISS] Building vector search index for case_id={case_id}")

        # ── 1. Fetch events from MongoDB ──────────────────────────────────────
        # Use a higher limit — deduplication keeps embedding count bounded
        from backend.app.repositories.event_repository import EventRepository
        _t_fetch = time.perf_counter()
        events = await EventRepository.list_by_case(case_id, org_id, limit=5000)
        fetch_time = time.perf_counter() - _t_fetch
        logger.info(f"[PROFILE] FAISS MongoDB fetch          {fetch_time:.3f}s  ({len(events)} events)")

        paths = cls.get_index_paths(case_id)
        if not events:
            logger.warning(f"[FAISS] No events found for case {case_id}. Deleting stale index.")
            for p in paths.values():
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            return False

        # ── 2. Generate sentences and deduplicate ─────────────────────────────
        _t_sent = time.perf_counter()
        sentence_to_idx: Dict[str, int] = {}     # sentence hash → index in unique_sentences
        unique_sentences: List[str] = []
        event_id_to_sent_idx: List[int] = []     # per-event: which unique sentence index

        for ev in events:
            sentence = cls.format_event_sentence(ev)
            h = hashlib.md5(sentence.encode("utf-8")).hexdigest()
            if h not in sentence_to_idx:
                sentence_to_idx[h] = len(unique_sentences)
                unique_sentences.append(sentence)
            event_id_to_sent_idx.append(sentence_to_idx[h])

        sent_time = time.perf_counter() - _t_sent
        cache_hits = len(events) - len(unique_sentences)
        logger.info(
            f"[PROFILE] FAISS sentence generation    {sent_time:.3f}s  "
            f"({len(events)} events → {len(unique_sentences)} unique, "
            f"{cache_hits} deduplicated)"
        )

        event_ids = [str(e["_id"]) for e in events]

        # ── 3. Compute embeddings for UNIQUE sentences only ───────────────────
        model = get_embedding_model()
        import asyncio
        loop = asyncio.get_running_loop()
        _t_embed = time.perf_counter()

        # Encode only the unique sentences — this is the main cost reduction
        unique_embeddings = await loop.run_in_executor(
            None,
            lambda: model.encode(
                unique_sentences,
                show_progress_bar=False,
                batch_size=32,
                normalize_embeddings=True,    # L2 norm for cosine-compatible search
            )
        )
        embed_time = time.perf_counter() - _t_embed
        logger.info(
            f"[PROFILE] FAISS embedding generation   {embed_time:.3f}s  "
            f"({len(unique_sentences)} unique sentences encoded)"
        )

        # ── 4. Build per-event embedding array using mapping ──────────────────
        _t_build = time.perf_counter()
        import faiss
        dimension = unique_embeddings.shape[1]

        # Build full embedding matrix (events × dim) by looking up deduplicated embeddings
        full_embeddings = np.array(
            [unique_embeddings[idx] for idx in event_id_to_sent_idx],
            dtype="float32"
        )

        index = faiss.IndexFlatIP(dimension)   # Inner product (cosine with normalized vecs)
        index.add(full_embeddings)
        build_time = time.perf_counter() - _t_build
        logger.info(f"[PROFILE] FAISS index build            {build_time:.3f}s  ({index.ntotal} vectors)")

        # ── 5. Save index and event ID mapping locally ────────────────────────
        _t_save = time.perf_counter()
        faiss.write_index(index, paths["index"])
        sentences_for_meta = [unique_sentences[idx] for idx in event_id_to_sent_idx]
        with open(paths["meta"], "wb") as f:
            pickle.dump({
                "event_ids":    event_ids,
                "sentences":    sentences_for_meta,
                "unique_count": len(unique_sentences),
                "total_events": len(events),
            }, f)
        save_time = time.perf_counter() - _t_save
        logger.info(f"[PROFILE] FAISS index save             {save_time:.3f}s")

        # Clean up transient arrays & trigger garbage collection
        del full_embeddings, unique_embeddings, unique_sentences
        import gc
        gc.collect()

        total_time = time.perf_counter() - _t_total
        logger.info(
            f"[PROFILE] FAISS TOTAL                  {total_time:.3f}s  "
            f"({index.ntotal} vectors, {cache_hits} embedding cache hits)"
        )
        return True

    @classmethod
    async def search_similar_events(cls, case_id: str, org_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Load FAISS index, embed query sentence, search, and fetch matching MongoDB documents."""
        import faiss
        paths = cls.get_index_paths(case_id)
        if not os.path.exists(paths["index"]) or not os.path.exists(paths["meta"]):
            logger.warning(f"[FAISS] Index not found for case {case_id}. Attempting rebuild...")
            success = await cls.index_case_events(case_id, org_id)
            if not success:
                return []

        # 1. Load index and mapping metadata
        index = faiss.read_index(paths["index"])
        with open(paths["meta"], "rb") as f:
            metadata = pickle.load(f)
        event_ids = metadata["event_ids"]

        # 2. Compute query embedding
        model = get_embedding_model()
        import asyncio
        loop = asyncio.get_running_loop()
        query_vector = await loop.run_in_executor(
            None,
            lambda: model.encode([query], show_progress_bar=False, normalize_embeddings=True)
        )

        # 3. Perform inner product search (cosine similarity with normalized vectors)
        search_limit = min(limit, index.ntotal)
        if search_limit <= 0:
            return []

        distances, indices = index.search(np.array(query_vector).astype("float32"), search_limit)

        # 4. Fetch matched events from MongoDB
        matched_ids = []
        for idx in indices[0]:
            if 0 <= idx < len(event_ids):
                matched_ids.append(ObjectId(event_ids[idx]))

        if not matched_ids:
            return []

        # Retrieve documents maintaining FAISS search rank order
        cursor = db_client.db["events"].find({"_id": {"$in": matched_ids}, "organization_id": ObjectId(org_id)})
        db_docs = {str(d["_id"]): d for d in await cursor.to_list(length=100)}

        ranked_results = []
        for idx, m_id in enumerate(matched_ids):
            str_id = str(m_id)
            if str_id in db_docs:
                doc = db_docs[str_id]
                doc["id"] = str_id
                doc["case_id"] = str(doc["case_id"])
                doc["evidence_id"] = str(doc["evidence_id"])
                doc["organization_id"] = str(doc["organization_id"])
                doc["_id"] = str_id
                doc["search_sentence"] = metadata["sentences"][indices[0][idx]]
                doc["distance"] = float(distances[0][idx])
                ranked_results.append(doc)

        return ranked_results
