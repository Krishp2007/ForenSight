from typing import List, Dict, Any
import numpy as np

class EmbeddingsEvaluator:
    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """Compute cosine similarity index between two vectors."""
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    @staticmethod
    def benchmark_providers(sentences: List[str]) -> List[Dict[str, Any]]:
        """Run embedding evaluations for MiniLM, BGE, and E5 models."""
        from . import get_embedder
        models = ["minilm", "bge", "e5"]
        benchmarks = []
        
        for m in models:
            try:
                embedder = get_embedder(m)
                vectors = embedder.encode(sentences)
                
                # Convert list outputs to numpy arrays if necessary
                if not isinstance(vectors, np.ndarray):
                    vectors = np.array(vectors)
                    
                # Calculate pairwise similarities
                similarities = []
                n = len(sentences)
                for i in range(n):
                    for j in range(i + 1, n):
                        sim = EmbeddingsEvaluator.cosine_similarity(vectors[i], vectors[j])
                        similarities.append(sim)
                        
                avg_sim = float(np.mean(similarities)) if similarities else 0.0
                std_sim = float(np.std(similarities)) if similarities else 0.0
                
                benchmarks.append({
                    "model": m,
                    "status": "success",
                    "embedding_dimension": vectors.shape[1],
                    "average_pairwise_similarity": avg_sim,
                    "standard_deviation": std_sim
                })
            except Exception as e:
                benchmarks.append({
                    "model": m,
                    "status": "failed",
                    "error": str(e),
                    "embedding_dimension": 0,
                    "average_pairwise_similarity": 0.0,
                    "standard_deviation": 0.0
                })
                
        return benchmarks
