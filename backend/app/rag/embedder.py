"""Local embedding generation using sentence-transformers (all-MiniLM-L6-v2)."""

from typing import Optional

_model = None
MODEL_NAME = "all-MiniLM-L6-v2"


def get_embedding_model():
    """Lazy-load and return the SentenceTransformer model singleton."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_text(text: str) -> list[float]:
    """Generate a 384-dimensional embedding for a single text string."""
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate 384-dimensional embeddings for a batch of text strings."""
    if not texts:
        return []
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()
