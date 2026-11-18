"""Verification script for Step E3: Query Rewriting for Follow-Up Questions."""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.rag.rewrite import rewrite_query
from app.rag.answer import answer_question, REFUSAL_ANSWER

print("=" * 70)
print("Step E3: Query Rewriting (Multi-Turn Follow-Ups) Verification")
print("=" * 70)

# 1. No History / Standalone Query (Should remain unchanged)
print("\n[Test 1] Initial Query with No History")
query1 = "What is the return policy for laptops?"
rewritten1 = rewrite_query(query1, history=[])
print(f"  -> Original:  '{query1}'")
print(f"  -> Rewritten: '{rewritten1}'")
assert rewritten1 == query1, "Query with empty history should not be altered!"
print("  -> Passed! Standalone query preserved.")

# 2. Multi-turn Follow-up: Earbuds Policy
print("\n[Test 2] Follow-Up Query: 'what about for earbuds?'")
history2 = [
    {"role": "user", "content": "What is your return policy?"},
    {
        "role": "assistant",
        "content": "You can return items within 30 days of delivery with the original receipt.",
    },
]
query2 = "what about for earbuds?"
rewritten2 = rewrite_query(query2, history=history2)
print(f"  -> Original:  '{query2}'")
print(f"  -> Rewritten: '{rewritten2}'")
assert "earbud" in rewritten2.lower()
assert any(w in rewritten2.lower() for w in ["return", "policy", "refund"])
print("  -> Passed! Rewritten query includes return/refund context and earbuds.")

# 3. Multi-turn Follow-up: City Delivery Availability
print("\n[Test 3] Follow-Up Query: 'in Pune?'")
history3 = [
    {"role": "user", "content": "Is express shipping available?"},
    {
        "role": "assistant",
        "content": "Express takes 1-2 business days for 150 rupees extra in select cities.",
    },
]
query3 = "in Pune?"
rewritten3 = rewrite_query(query3, history=history3)
print(f"  -> Original:  '{query3}'")
print(f"  -> Rewritten: '{rewritten3}'")
assert "pune" in rewritten3.lower()
assert any(w in rewritten3.lower() for w in ["shipping", "delivery", "express"])
print("  -> Passed! Elliptical fragment 'in Pune?' contextualized with shipping.")

# 4. End-to-End Grounded Answer for Multi-turn 'in Pune?'
print("\n[Test 4] End-to-End Grounded Answer for 'in Pune?' with History")
ans4 = answer_question(query3, history=history3)
print(f"  -> Answer: {ans4.answer}")
print(f"  -> Sources: {ans4.sources}")
assert any(src.startswith("shipping") for src in ans4.sources)
assert any(w in ans4.answer.lower() for w in ["not available", "no", "not offered", "only"])
print("  -> Passed! Grounded answer correctly explains express shipping is not available in Pune.")

# 5. End-to-End Grounded Answer for Multi-turn 'what about for earbuds?'
print("\n[Test 5] End-to-End Grounded Answer for 'what about for earbuds?' with History")
ans5 = answer_question(query2, history=history2)
print(f"  -> Answer: {ans5.answer}")
print(f"  -> Sources: {ans5.sources}")
assert any(src.startswith("returns") for src in ans5.sources)
assert any(w in ans5.answer.lower() for w in ["cannot", "not", "no"])
print("  -> Passed! Grounded answer correctly explains earbuds cannot be returned.")

print("\n" + "=" * 70)
print("ALL QUERY REWRITING (STEP E3) TESTS PASSED SUCCESSFULLY!")
print("=" * 70)
