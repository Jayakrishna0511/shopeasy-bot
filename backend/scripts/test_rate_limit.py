"""Verification script for Step D4: Input Length Caps and Sliding-Window Rate Limiting."""

import json
import urllib.request
import urllib.error
from unittest.mock import Mock

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import HTTPException
from app.core.rate_limit import check_rate_limit, _request_history
from app.models.user import User

BASE_URL = "http://127.0.0.1:8000/api"

def make_req(path: str, method: str = "POST", headers: dict = None, body: dict = None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    h = headers or {}
    if body and "Content-Type" not in h:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8")), resp.headers
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        try:
            err_body = json.loads(raw)
        except Exception:
            err_body = {"detail": raw}
        return e.code, err_body, e.headers


print("=" * 70)
print("Step D4: Rate Limiting & Input Length Caps Verification")
print("=" * 70)

# 1. Test Input Length Cap (1,005 characters fails with 422)
print("\n[Test 1] Input Length Cap: Message with 1,005 characters")
giant_msg = "A" * 1005
status, err_resp, _ = make_req("/chat", headers={"X-User-Id": "arjun"}, body={"message": giant_msg})
print(f"  Status: {status} (Expected 422)")
print(f"  Error Detail: {err_resp.get('detail')}")
assert status == 422
print("  -> Passed! Message > 1000 characters successfully rejected.")

# 2. Test Input Length Cap: Valid 150 characters message passes validation
print("\n[Test 2] Input Length Cap: Valid message with 150 characters")
valid_msg = "Can you help me check if express delivery is available in Hyderabad?"
status, valid_resp, _ = make_req("/chat", headers={"X-User-Id": "arjun"}, body={"message": valid_msg})
print(f"  Status: {status} (Expected 200)")
assert status == 200
print("  -> Passed! Valid length message accepted.")

# 3. Test Rate Limiter Logic: Sliding Window
print("\n[Test 3] Rate Limiter Unit Test: 15 requests allowed within 60-second window")
user_a = User(id="test_user_a", name="Test User A")
mock_req = Mock()
_request_history.clear()

# Send 15 requests
for i in range(15):
    check_rate_limit(mock_req, current_user=user_a, max_requests=15, window_seconds=60)
print("  -> Successfully allowed 15 requests within window.")

# 16th request must raise HTTPException 429
print("\n[Test 4] 16th Request within Window: Must trigger 429 Too Many Requests")
try:
    check_rate_limit(mock_req, current_user=user_a, max_requests=15, window_seconds=60)
    assert False, "Expected 429 HTTPException was not raised!"
except HTTPException as e:
    print(f"  -> Caught Expected HTTPException: Status {e.status_code}")
    print(f"  -> Detail: {e.detail}")
    print(f"  -> Headers: {e.headers}")
    assert e.status_code == 429
    assert "Retry-After" in e.headers
    print("  -> Passed! Rate limit enforced with Retry-After header.")

# 4. User Isolation Check: User B is NOT blocked
print("\n[Test 5] User Isolation: User B ('priya') is NOT affected by User A's rate limit")
user_b = User(id="priya", name="Priya Sharma")
# User B should be able to make a request without exception
check_rate_limit(mock_req, current_user=user_b, max_requests=15, window_seconds=60)
print("  -> Passed! User B request succeeded without being rate-limited.")

print("\n" + "=" * 70)
print("ALL RATE LIMITING & INPUT LENGTH CHECKS PASSED SUCCESSFULLY!")
print("=" * 70)
