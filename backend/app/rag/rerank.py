"""Cross-Encoder Reranking module for second-stage retrieval refinement.

Architecture (Two-Stage Retrieval):
1. First Stage (High Recall): Hybrid Search (pgvector + FTS) retrieves ~15-20 candidates.
2. Second Stage (High Precision): Cross-Encoder performs full cross-attention on (query, chunk) pairs
   to score deep semantic relevance and filter down to top_k (e.g., 4) most accurate chunks.
"""

from dataclasses import dataclass
import sys
from pathlib import Path
from typing import List, Optional

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sentence_transformers import CrossEncoder
from app.rag.hybrid import HybridChunk

# Standard lightweight, fast cross-encoder benchmark model (~80MB)
MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_reranker: Optional[CrossEncoder] = None


def get_reranker() -> CrossEncoder:
    """Singleton getter for the Cross-Encoder model."""
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(MODEL_NAME, max_length=512)
    return _reranker


def rerank_chunks(
    query: str,
    chunks: List[HybridChunk],
    top_k: int = 4,
    min_score: Optional[float] = None,
) -> List[HybridChunk]:
    """Rerank candidate chunks using cross-attention scoring.

    Args:
        query: Customer's search query or question.
        chunks: Broad list of candidate chunks from Hybrid Search (e.g., 10-20 chunks).
        top_k: Number of highest-scoring chunks to keep.
        min_score: Optional minimum relevance score threshold (log-odds / logits).

    Returns:
        Sorted list of top_k chunks with their rerank_score populated.
    """
    if not chunks:
        return []

    # If only 1 chunk was retrieved, populate score and return
    if len(chunks) == 1:
        reranker = get_reranker()
        score = float(reranker.predict([(query, chunks[0].chunk_text)])[0])
        chunks[0].rerank_score = score
        if min_score is not None and score < min_score:
            return []
        return chunks

    # Build (query, document) pairs for the cross-encoder
    pairs = [(query, chunk.chunk_text) for chunk in chunks]
    reranker = get_reranker()
    scores = reranker.predict(pairs)

    # Attach rerank score to each chunk
    scored_chunks: List[tuple[HybridChunk, float]] = []
    for chunk, score in zip(chunks, scores):
        chunk.rerank_score = float(score)
        if min_score is not None and chunk.rerank_score < min_score:
            continue
        scored_chunks.append((chunk, chunk.rerank_score))

    # Sort descending by cross-encoder score
    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    return [chunk for chunk, _ in scored_chunks[:top_k]]
