"""Verification script for Step E2: Cross-Encoder Reranking (retrieve ~15-20, keep 4)."""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.rag.hybrid import hybrid_search
from app.rag.rerank import rerank_chunks
from app.rag.answer import answer_question, REFUSAL_ANSWER

print("=" * 70)
print("Step E2: Cross-Encoder Reranking Verification")
print("=" * 70)

# 1. Test Candidate Retrieval + Cross-Encoder Scoring
print("\n[Test 1] Cross-Encoder Scoring on Broad Candidates")
query1 = "How long do I have to return an item?"
candidates1 = hybrid_search(query1, top_k=15)
assert len(candidates1) > 0, "No candidates returned from hybrid search!"
print(f"  -> Retrieved {len(candidates1)} candidates from Hybrid Search.")

reranked1 = rerank_chunks(query1, candidates1, top_k=4)
assert len(reranked1) <= 4, "Reranked list exceeded top_k!"
assert reranked1[0].rerank_score is not None, "Rerank score was not populated!"
print(f"  -> Top Reranked Chunk: {reranked1[0].source} (Cross-Encoder score: {reranked1[0].rerank_score:.4f})")
print(f"  -> Excerpt: {reranked1[0].chunk_text[:100]}...")
assert "returns" in reranked1[0].source
print("  -> Passed! Top reranked chunk is returns policy.")

# 2. Test Nuanced Policy Exception: Opened Earbuds
print("\n[Test 2] Nuanced Policy Exception: 'Can I return opened earbuds?'")
query2 = "Can I return opened earbuds?"
candidates2 = hybrid_search(query2, top_k=15)
reranked2 = rerank_chunks(query2, candidates2, top_k=4)
assert len(reranked2) > 0, "No reranked results for earbuds query!"
top_chunk = reranked2[0]
print(f"  -> Top Reranked Chunk: {top_chunk.source} (Score: {top_chunk.rerank_score:.4f})")
print(f"  -> Excerpt: {top_chunk.chunk_text[:120]}...")
# Check that the chunk text mentions earbuds
assert "earbuds" in top_chunk.chunk_text.lower() or "cannot be returned" in top_chunk.chunk_text.lower()
print("  -> Passed! Cross-Encoder successfully surfaced the non-returnable earbuds exception.")

# 3. Test Technical Error Resolution: Error P-2210
print("\n[Test 3] Technical Error Code: 'What does error P-2210 mean?'")
query3 = "What does error P-2210 mean?"
candidates3 = hybrid_search(query3, top_k=15)
reranked3 = rerank_chunks(query3, candidates3, top_k=4)
assert len(reranked3) > 0
print(f"  -> Top Reranked Chunk: {reranked3[0].source} (Score: {reranked3[0].rerank_score:.4f})")
print(f"  -> Excerpt: {reranked3[0].chunk_text[:120]}...")
assert "P-2210" in reranked3[0].chunk_text
print("  -> Passed! Exact error code chunk ranked #1 by Cross-Encoder.")

# 4. Off-Topic Query Safe Refusal
print("\n[Test 4] Off-Topic Query Refusal: 'What is the capital of Japan?'")
off_topic_ans = answer_question("What is the capital of Japan?")
print(f"  -> Answer: {off_topic_ans.answer}")
assert off_topic_ans.answer == REFUSAL_ANSWER, f"Expected exact refusal, got: {off_topic_ans.answer}"
print("  -> Passed! Off-topic query safely refused.")

# 5. End-to-End Grounded Answer for Earbuds
print("\n[Test 5] End-to-End Grounded Answer for 'Can I return opened earbuds?'")
ans = answer_question("Can I return opened earbuds?")
print(f"  -> Answer: {ans.answer}")
print(f"  -> Sources: {ans.sources}")
assert any(word in ans.answer.lower() for word in ["cannot", "not", "no"])
assert "earbuds" in ans.answer.lower()
print("  -> Passed! Grounded answer correctly explains that opened earbuds cannot be returned.")

print("\n" + "=" * 70)
print("ALL CROSS-ENCODER RERANKING (STEP E2) TESTS PASSED SUCCESSFULLY!")
print("=" * 70)
