"""Test script for Step B3: Vector Retrieval and Grounded Answering.

Tests the 3 required sample questions from Section 8 of AGENTS.md.
Usage:
    cd backend
    python scripts/test_rag.py
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.rag.answer import REFUSAL_ANSWER, answer_question
from app.rag.retrieve import retrieve_chunks

TEST_QUESTIONS = [
    "How long do I have to return an item?",
    "My package arrived broken, what do I do?",
    "What is the capital of Japan?",
    "i want to return my buds because the are damaged",
    "Can I return earbuds?",
]


def run_tests() -> None:
    print("=" * 70)
    print("ShopEasy RAG Pipeline Verification (Step B3)")
    print("=" * 70)

    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[Test {i}] Question: \"{question}\"")
        print("-" * 50)

        # 1. Test Retrieval
        chunks = retrieve_chunks(question, top_k=2, distance_threshold=0.75)
        if chunks:
            top_chunk = chunks[0]
            print(f"  -> Retrieved {len(chunks)} chunk(s).")
            print(f"  -> Best Match: {top_chunk.source} (Similarity: {top_chunk.similarity:.2%}, Distance: {top_chunk.distance})")
            preview = top_chunk.chunk_text.strip().split("\n")[0]
            print(f"  -> Excerpt: {preview}...")
        else:
            print("  -> Retrieved 0 chunks (below similarity threshold 0.75 - irrelevant).")

        # 2. Test Answer Function
        result = answer_question(question, distance_threshold=0.75)
        print(f"  -> Answer: {result.answer}")
        if result.sources:
            print(f"  -> Cited Sources: {', '.join(result.sources)}")

    print("\n" + "=" * 70)
    print("Verification complete.")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
