"""Text chunker with word-based windowing and overlap."""


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 40) -> list[str]:
    """Split text into chunks of `chunk_size` words with `overlap` words shared between adjacent chunks.

    Args:
        text: The source text to split.
        chunk_size: Number of words per chunk (default 200).
        overlap: Number of overlapping words between consecutive chunks (default 40).

    Returns:
        A list of string chunks.
    """
    words = text.split()
    if not words:
        return []

    if len(words) <= chunk_size:
        return [text.strip()]

    step = max(1, chunk_size - overlap)
    chunks: list[str] = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
        start += step

    return chunks
