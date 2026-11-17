"""Document ingestion pipeline for ShopEasy RAG."""

import re
import sys
from pathlib import Path
from typing import Optional

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import delete, func, select

from app.db import SessionLocal
from app.models import Chunk, Document
from app.rag.chunker import chunk_text
from app.rag.embedder import embed_texts

DATA_DOCS_DIR = backend_dir / "data" / "docs"


def extract_title_from_markdown(content: str, fallback: str) -> str:
    """Extract first H1 title from markdown content, or fallback."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return fallback.replace("_", " ").replace(".md", "").title()


def ingest_documents(docs_dir: Optional[Path] = None) -> dict[str, int]:
    """Ingest markdown policy documents into documents and chunks tables.

    Returns:
        dict with counts of processed documents and created chunks.
    """
    target_dir = docs_dir or DATA_DOCS_DIR
    if not target_dir.exists():
        raise FileNotFoundError(f"Documents directory not found: {target_dir}")

    doc_files = sorted(list(target_dir.glob("*.md")))
    if not doc_files:
        print(f"No markdown documents found in {target_dir}")
        return {"documents": 0, "chunks": 0}

    session = SessionLocal()
    total_docs = 0
    total_chunks = 0

    try:
        for filepath in doc_files:
            filename = filepath.name
            raw_text = filepath.read_text(encoding="utf-8").strip()
            if not raw_text:
                continue

            title = extract_title_from_markdown(raw_text, filename)

            # 1. Upsert Document record
            stmt = select(Document).where(Document.source == filename)
            doc = session.execute(stmt).scalar_one_or_none()
            if doc is None:
                doc = Document(source=filename, title=title)
                session.add(doc)
                session.flush()
            else:
                doc.title = title
                session.flush()

            # 2. Clean up any existing chunks for this document
            session.execute(delete(Chunk).where(Chunk.document_id == doc.id))

            # 3. Chunk the text (~200 words, 40 overlap)
            chunks = chunk_text(raw_text, chunk_size=200, overlap=40)
            if not chunks:
                continue

            # 4. Generate batch embeddings
            embeddings = embed_texts(chunks)

            # 5. Insert chunks
            for idx, (chunk_str, emb) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"{filename}:{idx}"
                chunk_record = Chunk(
                    id=chunk_id,
                    document_id=doc.id,
                    chunk_text=chunk_str,
                    chunk_index=idx,
                    source=filename,
                    page=1,
                    chunk_metadata={
                        "source": filename,
                        "title": title,
                        "chunk_index": idx,
                    },
                    embedding=emb,
                    tsv=func.to_tsvector("english", chunk_str),
                )
                session.add(chunk_record)
                total_chunks += 1

            total_docs += 1
            print(f"Ingested '{filename}' -> {len(chunks)} chunk(s)")

        session.commit()
        print(f"\nIngestion complete! Total documents: {total_docs}, Total chunks: {total_chunks}")
        return {"documents": total_docs, "chunks": total_chunks}

    except Exception as e:
        session.rollback()
        print(f"Error during ingestion: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    ingest_documents()
