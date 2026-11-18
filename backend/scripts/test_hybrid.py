"""Verification script for Step E1: Hybrid Search (pgvector + PostgreSQL Full-Text RRF)."""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.rag.hybrid import hybrid_search
from app.rag.answer import answer_question, REFUSAL_ANSWER

print("=" * 70)
print("Step E1: Hybrid Search (pgvector + tsvector RRF) Verification")
print("=" * 70)

# 1. Exact Keyword / Error Code Query (FTS strength)
print("\n[Test 1] Exact Code Query: 'What should I do for payment error P-1042?'")
results1 = hybrid_search("What should I do for payment error P-1042?", top_k=3)
assert len(results1) > 0, "No results returned for error P-1042!"
top1 = results1[0]
print(f"  -> Top Match: {top1.source} (RRF Score: {top1.rrf_score:.6f})")
print(f"  -> Vector Rank: {top1.vector_rank}, FTS Rank: {top1.fts_rank}")
print(f"  -> Excerpt: {top1.chunk_text[:120]}...")
assert "payments" in top1.source
print("  -> Passed! Exact error code matched payments policy.")

# 2. Semantic Synonym Query (Vector strength)
print("\n[Test 2] Semantic Synonym Query: 'my package arrived smashed into pieces'")
results2 = hybrid_search("my package arrived smashed into pieces", top_k=3)
assert len(results2) > 0, "No results returned for smashed package!"
top2 = results2[0]
print(f"  -> Top Match: {top2.source} (RRF Score: {top2.rrf_score:.6f})")
print(f"  -> Vector Rank: {top2.vector_rank}, FTS Rank: {top2.fts_rank}")
print(f"  -> Excerpt: {top2.chunk_text[:120]}...")
assert "damaged" in top2.source
print("  -> Passed! Semantic synonym matched damaged items policy.")

# 3. Dual-Match Query (Both Vector & FTS match keywords and concepts)
print("\n[Test 3] Dual-Match Query: 'return policy 30 days receipt'")
results3 = hybrid_search("return policy 30 days receipt", top_k=3)
assert len(results3) > 0
top3 = results3[0]
print(f"  -> Top Match: {top3.source} (RRF Score: {top3.rrf_score:.6f})")
print(f"  -> Vector Rank: {top3.vector_rank}, FTS Rank: {top3.fts_rank}")
assert top3.vector_rank is not None and top3.fts_rank is not None, "Expected dual match in both vector and FTS!"
assert "returns" in top3.source
print("  -> Passed! Successfully fused ranks from both vector and FTS.")

# 4. Off-Topic Query (Should return 0 chunks / trigger refusal)
print("\n[Test 4] Off-Topic Query: 'What is the population of Tokyo?'")
results4 = hybrid_search("What is the population of Tokyo?", top_k=3)
print(f"  -> Returned Chunks: {len(results4)}")
ans_offtopic = answer_question("What is the population of Tokyo?")
print(f"  -> Answer: {ans_offtopic.answer}")
assert ans_offtopic.answer == REFUSAL_ANSWER
print("  -> Passed! Off-topic query safely refused.")

# 5. Full End-to-End Grounded Answer for Error Code
print("\n[Test 5] End-to-End Grounded Answer for 'Error P-1042':")
ans_p1042 = answer_question("What should I do for payment error P-1042?")
print(f"  -> Answer: {ans_p1042.answer}")
print(f"  -> Sources: {ans_p1042.sources}")
assert "10 minutes" in ans_p1042.answer.lower()
print("  -> Passed! Grounded answer correctly explains waiting 10 minutes.")

print("\n" + "=" * 70)
print("ALL HYBRID SEARCH (RRF) TESTS PASSED SUCCESSFULLY!")
print("=" * 70)
