"""Hybrid Search Engine combining dense pgvector and sparse PostgreSQL full-text search.

Uses Reciprocal Rank Fusion (RRF) to merge:
1. Vector similarity search (semantic understanding, synonyms, conceptual match)
2. PostgreSQL full-text search (exact keywords, error codes, numbers, acronyms)

RRF Formula:
    Score(d) = sum(1 / (k + rank_i(d))) for each search method i
"""

from dataclasses import dataclass
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import func, select
from app.db import SessionLocal
from app.models.chunk import Chunk
from app.rag.embedder import embed_text

DEFAULT_RRF_K = 60


@dataclass
class HybridChunk:
    id: str
    source: str
    chunk_text: str
    chunk_index: int
    rrf_score: float
    vector_rank: Optional[int] = None
    fts_rank: Optional[int] = None
    vector_distance: Optional[float] = None
    fts_score: Optional[float] = None
    rerank_score: Optional[float] = None


def hybrid_search(
    query: str,
    top_k: int = 4,
    vector_candidates: int = 10,
    fts_candidates: int = 10,
    rrf_k: int = DEFAULT_RRF_K,
    distance_threshold: float = 0.85,
) -> List[HybridChunk]:
    """Execute hybrid search using pgvector + PostgreSQL tsvector and merge via RRF.

    Args:
        query: User search query or question.
        top_k: Number of final merged chunks to return.
        vector_candidates: Number of candidates to retrieve from vector search.
        fts_candidates: Number of candidates to retrieve from keyword search.
        rrf_k: Smoothing constant for Reciprocal Rank Fusion (standard default: 60).
        distance_threshold: Cutoff for vector candidates to reject completely off-topic queries.

    Returns:
        List of HybridChunk objects sorted by descending RRF score.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    session = SessionLocal()
    try:
        # 1. Dense Vector Search (pgvector)
        query_emb = embed_text(clean_query)
        distance_col = Chunk.embedding.cosine_distance(query_emb).label("distance")

        vector_stmt = (
            select(Chunk, distance_col)
            .where(distance_col <= distance_threshold)
            .order_by(distance_col.asc())
            .limit(vector_candidates)
        )
        vector_results = session.execute(vector_stmt).all()

        # 2. Sparse Full-Text Keyword Search (PostgreSQL tsvector)
        ts_query = func.websearch_to_tsquery("english", clean_query)
        rank_col = func.ts_rank_cd(Chunk.tsv, ts_query).label("fts_rank_score")

        fts_stmt = (
            select(Chunk, rank_col)
            .where(Chunk.tsv.op("@@")(ts_query))
            .order_by(rank_col.desc())
            .limit(fts_candidates)
        )
        fts_results = session.execute(fts_stmt).all()

        if not fts_results:
            ts_query_plain = func.plainto_tsquery("english", clean_query)
            fts_stmt_plain = (
                select(Chunk, rank_col)
                .where(Chunk.tsv.op("@@")(ts_query_plain))
                .order_by(rank_col.desc())
                .limit(fts_candidates)
            )
            fts_results = session.execute(fts_stmt_plain).all()

        # 3. Reciprocal Rank Fusion (RRF)
        # Map: chunk_id -> chunk_data & ranks
        chunk_map: Dict[str, Chunk] = {}
        vector_ranks: Dict[str, int] = {}
        vector_distances: Dict[str, float] = {}
        fts_ranks: Dict[str, int] = {}
        fts_scores: Dict[str, float] = {}

        for rank, (chunk, dist) in enumerate(vector_results, 1):
            chunk_map[chunk.id] = chunk
            vector_ranks[chunk.id] = rank
            vector_distances[chunk.id] = round(float(dist), 4)

        for rank, (chunk, score) in enumerate(fts_results, 1):
            chunk_map[chunk.id] = chunk
            fts_ranks[chunk.id] = rank
            fts_scores[chunk.id] = round(float(score), 4)

        if not chunk_map:
            return []

        # Calculate combined RRF score for all candidate chunks
        fused_chunks: List[HybridChunk] = []
        for chunk_id, chunk in chunk_map.items():
            score = 0.0
            v_rank = vector_ranks.get(chunk_id)
            f_rank = fts_ranks.get(chunk_id)

            if v_rank is not None:
                score += 1.0 / (rrf_k + v_rank)
            if f_rank is not None:
                score += 1.0 / (rrf_k + f_rank)

            fused_chunks.append(
                HybridChunk(
                    id=chunk.id,
                    source=chunk.source,
                    chunk_text=chunk.chunk_text,
                    chunk_index=chunk.chunk_index,
                    rrf_score=round(score, 6),
                    vector_rank=v_rank,
                    fts_rank=f_rank,
                    vector_distance=vector_distances.get(chunk_id),
                    fts_score=fts_scores.get(chunk_id),
                )
            )

        # 4. Sort by RRF score descending and return top_k
        fused_chunks.sort(key=lambda c: c.rrf_score, reverse=True)
        return fused_chunks[:top_k]

    finally:
        session.close()
