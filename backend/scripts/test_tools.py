"""Verification script for Step D2: Tools and SQL Parameter-Bound Queries."""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.agent.tools import (
    search_docs,
    get_order_status,
    list_user_orders,
    cancel_order,
    TOOL_DEFINITIONS,
)

print("=" * 70)
print("Step D2: Tools & Security Boundaries Verification")
print("=" * 70)

# 1. Test search_docs
print("\n[Test 1] Tool: search_docs('earbuds return policy')")
doc_res = search_docs("earbuds return policy")
print(f"  -> Found: {doc_res['found']}, Sources: {doc_res['sources']}")
assert doc_res["found"] is True
assert "returns_and_refunds.md" in doc_res["sources"]

# 2. Test get_order_status for own order (Ravi -> A1001, delivered)
print("\n[Test 2] Tool: get_order_status(order_id='A1001', user_id='ravi')")
status_res = get_order_status("A1001", "ravi")
print(f"  -> Found: {status_res['found']}")
print(f"  -> Item: {status_res['item']}, Status: {status_res['status']}, Can Cancel: {status_res['can_cancel']}")
assert status_res["found"] is True
assert status_res["status"] == "delivered"
assert status_res["can_cancel"] is False

# 3. Test get_order_status for processing order (Ravi -> A1002, processing)
print("\n[Test 3] Tool: get_order_status(order_id='A1002', user_id='ravi')")
status_proc = get_order_status("A1002", "ravi")
print(f"  -> Found: {status_proc['found']}")
print(f"  -> Item: {status_proc['item']}, Status: {status_proc['status']}, Can Cancel: {status_proc['can_cancel']}")
assert status_proc["found"] is True
assert status_proc["status"] == "processing"
assert status_proc["can_cancel"] is True

# 4. Security Check: Cross-Tenant Data Isolation (Ravi querying Priya's order)
print("\n[Test 4] Security Check: Cross-Tenant Isolation (Ravi querying Priya's order 'B1001')")
leak_check = get_order_status("B1001", "ravi")
print(f"  -> Found: {leak_check['found']}")
print(f"  -> Error Response: {leak_check.get('error')}")
assert leak_check["found"] is False
assert "No order found" in leak_check["error"]

# 5. Test cancel_order for non-cancellable order (Ravi -> A1001, delivered)
print("\n[Test 5] Policy Enforcement: cancel_order('A1001', 'ravi') on delivered item")
cancel_del = cancel_order("A1001", "ravi")
print(f"  -> Success: {cancel_del['success']}")
print(f"  -> Error: {cancel_del.get('error')}")
assert cancel_del["success"] is False
assert "cannot be cancelled" in cancel_del["error"]

# 6. Test cancel_order for eligible order (Ravi -> A1002, processing)
print("\n[Test 6] Policy Enforcement: cancel_order('A1002', 'ravi') on processing item")
cancel_proc = cancel_order("A1002", "ravi")
print(f"  -> Success: {cancel_proc['success']}")
print(f"  -> Status: {cancel_proc.get('cancellation_status')}")
print(f"  -> Message: {cancel_proc.get('message')}")
assert cancel_proc["success"] is True
assert cancel_proc["cancellation_status"] == "pending_confirmation"
assert cancel_proc["requires_approval"] is True

# 7. Test list_user_orders (Ravi)
print("\n[Test 7] Tool: list_user_orders('ravi')")
orders_res = list_user_orders("ravi", limit=3)
print(f"  -> Count: {orders_res['count']} orders found:")
for o in orders_res["orders"]:
    print(f"     * [{o['order_id']}] {o['item']} - ₹{o['price']} ({o['status']})")
assert orders_res["count"] > 0
assert all(o["order_id"].startswith("A") for o in orders_res["orders"])

# 8. Verify Tool Schemas (JSON Schema validation)
print("\n[Test 8] Tool Schema Definitions for LLM Function Calling:")
print(f"  -> Registered Tools: {[t['name'] for t in TOOL_DEFINITIONS]}")
assert len(TOOL_DEFINITIONS) == 4

print("\n" + "=" * 70)
print("ALL TOOL & SECURITY TESTS PASSED SUCCESSFULLY!")
print("=" * 70)
