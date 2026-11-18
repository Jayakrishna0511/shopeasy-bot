"""Vector retrieval module using pgvector cosine distance and similarity threshold."""

from dataclasses import dataclass
import sys
from pathlib import Path
from typing import List

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Chunk
from app.rag.embedder import embed_text


@dataclass
class RetrievedChunk:
    id: str
    source: str
    chunk_text: str
    distance: float
    similarity: float
    chunk_index: int


def retrieve_chunks(
    query: str,
    top_k: int = 4,
    distance_threshold: float = 0.70,
) -> List[RetrievedChunk]:
    """Retrieve the top_k most similar document chunks for a query from Neon pgvector.

    Args:
        query: User search query or question.
        top_k: Maximum number of chunks to return.
        distance_threshold: Maximum allowed cosine distance (1 - cosine_similarity).
            Chunks with distance higher than this threshold are filtered out as irrelevant.

    Returns:
        List of RetrievedChunk objects ordered by ascending distance (highest similarity first).
    """
    if not query.strip():
        return []

    query_emb = embed_text(query)
    session = SessionLocal()

    try:
        distance_col = Chunk.embedding.cosine_distance(query_emb).label("distance")
        stmt = (
            select(Chunk, distance_col)
            .where(distance_col <= distance_threshold)
            .order_by(distance_col.asc())
            .limit(top_k)
        )
        results = session.execute(stmt).all()

        retrieved: List[RetrievedChunk] = []
        for chunk, distance in results:
            dist_val = float(distance)
            sim_val = round(1.0 - dist_val, 4)
            retrieved.append(
                RetrievedChunk(
                    id=chunk.id,
                    source=chunk.source,
                    chunk_text=chunk.chunk_text,
                    distance=round(dist_val, 4),
                    similarity=sim_val,
                    chunk_index=chunk.chunk_index,
                )
            )

        return retrieved
    finally:
        session.close()
