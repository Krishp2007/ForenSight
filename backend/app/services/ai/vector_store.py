import os
import pickle
import logging
import numpy as np
import faiss
from typing import List, Dict, Any

# Suppress harmless HuggingFace hub rate limit/symlinks warning logs
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from sentence_transformers import SentenceTransformer
from bson import ObjectId

from backend.app.db.mongodb import db_client
from backend.app.config import settings

logger = logging.getLogger(__name__)

# Initialize sentence transformer model lazily to avoid loading times on import
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
        # Force model cache path inside the workspace to keep it self-contained
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
            "meta": os.path.join(base_dir, "metadata.pkl")
        }

    @classmethod
    def format_event_sentence(cls, event: Dict[str, Any]) -> str:
        """Translate a CFM event record into a clear natural language statement."""
        ts = event.get("timestamp")
        ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
        subj = event.get("subject", "unknown subject")
        act = event.get("action", "performed action")
        obj = event.get("object", "unknown target")
        sev = event.get("severity", "info")
        return f"At {ts_str}, {subj} performed '{act}' on '{obj}'. Threat Severity: {sev}."

    @classmethod
    async def index_case_events(cls, case_id: str, org_id: str) -> bool:
        """Load all events for a case, generate embeddings, and build the FAISS index."""
        logger.info(f"Building vector search index for case_id={case_id}")
        
        # 1. Fetch relevant events from MongoDB (capping at 2000 to keep SentenceTransformer fast, prioritizing critical/high/medium/low severity)
        from bson import ObjectId
        query_non_info = {
            "case_id": ObjectId(case_id),
            "organization_id": ObjectId(org_id),
            "severity": {"$ne": "info"}
        }
        cursor = db_client.db["events"].find(query_non_info).sort("timestamp", 1).limit(2000)
        events = await cursor.to_list(length=2000)
        
        # If we have less than 1000 non-info events, load info events too up to total 2000 limit
        if len(events) < 1000:
            remaining_limit = 2000 - len(events)
            query_info = {
                "case_id": ObjectId(case_id),
                "organization_id": ObjectId(org_id),
                "severity": "info"
            }
            cursor_info = db_client.db["events"].find(query_info).sort("timestamp", 1).limit(remaining_limit)
            info_events = await cursor_info.to_list(length=remaining_limit)
            events.extend(info_events)
            
        if not events:
            logger.warning(f"No events found to index for case {case_id}.")
            return False
            
        # 2. Convert events to sentence texts
        sentences = [cls.format_event_sentence(e) for e in events]
        event_ids = [str(e["_id"]) for e in events]
        
        # 3. Compute Embeddings
        model = get_embedding_model()
        # Compute embeddings in a background execution pool
        import asyncio
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(None, lambda: model.encode(sentences, show_progress_bar=False))
        
        # 4. Build FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(embeddings).astype("float32"))
        
        # 5. Save index and event ID mapping locally
        paths = cls.get_index_paths(case_id)
        faiss.write_index(index, paths["index"])
        with open(paths["meta"], "wb") as f:
            pickle.dump({"event_ids": event_ids, "sentences": sentences}, f)
            
        logger.info(f"Successfully built FAISS index with {index.ntotal} vectors for case {case_id}.")
        return True

    @classmethod
    async def search_similar_events(cls, case_id: str, org_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Load FAISS index, embed query sentence, search, and fetch matching MongoDB documents."""
        paths = cls.get_index_paths(case_id)
        if not os.path.exists(paths["index"]) or not os.path.exists(paths["meta"]):
            logger.warning(f"FAISS index files not found for case {case_id}. Attempting automatic rebuild...")
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
        query_vector = await loop.run_in_executor(None, lambda: model.encode([query], show_progress_bar=False))
        
        # 3. Perform L2 distance search
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
            
        # Retrieve documents maintaining the FAISS search rank order
        cursor = db_client.db["events"].find({"_id": {"$in": matched_ids}, "organization_id": ObjectId(org_id)})
        db_docs = {str(d["_id"]): d for d in await cursor.to_list(length=100)}
        
        ranked_results = []
        for idx, m_id in enumerate(matched_ids):
            str_id = str(m_id)
            if str_id in db_docs:
                doc = db_docs[str_id]
                # Convert ObjectIds to strings for json friendliness
                doc["id"] = str_id
                doc["case_id"] = str(doc["case_id"])
                doc["evidence_id"] = str(doc["evidence_id"])
                doc["organization_id"] = str(doc["organization_id"])
                doc["_id"] = str_id
                # Append matching sentence metadata and search distance
                doc["search_sentence"] = metadata["sentences"][indices[0][idx]]
                doc["distance"] = float(distances[0][idx])
                ranked_results.append(doc)
                
        return ranked_results
