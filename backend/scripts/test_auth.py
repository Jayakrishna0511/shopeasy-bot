"""Verification script for Step D1: Authentication & User Identity."""

import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000/api"

def make_req(path: str, method: str = "GET", headers: dict = None, body: dict = None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    h = headers or {}
    if body and "Content-Type" not in h:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = json.loads(e.read().decode("utf-8")) if e.fp else {}
        return e.code, err_body


print("=" * 60)
print("Step D1: Authentication & User Identity Verification")
print("=" * 60)

# 1. Test GET /api/auth/users
status, users = make_req("/auth/users")
print(f"\n[Test 1] List Available Demo Users:")
print(f"  Status: {status}, Found {len(users)} users:")
for u in users:
    print(f"   - {u['id']}: {u['name']} (Premium: {u['is_premium']})")
assert status == 200
assert len(users) >= 3
assert any(u["id"] == "ravi" and u["is_premium"] is True for u in users)

# 2. Test GET /api/auth/me with default fallback (ravi)
status, me = make_req("/auth/me")
print(f"\n[Test 2] Auth Me (Default Fallback):")
print(f"  Status: {status}, Resolved: {me['id']} ({me['name']})")
assert status == 200
assert me["id"] == "ravi"

# 3. Test GET /api/auth/me with X-User-Id: priya
status, me_priya = make_req("/auth/me", headers={"X-User-Id": "priya"})
print(f"\n[Test 3] Auth Me (X-User-Id: priya):")
print(f"  Status: {status}, Resolved: {me_priya['id']} ({me_priya['name']}, Premium: {me_priya['is_premium']})")
assert status == 200
assert me_priya["id"] == "priya"
assert me_priya["is_premium"] is False

# 4. Test GET /api/auth/me with Bearer token
status, me_arjun = make_req("/auth/me", headers={"Authorization": "Bearer arjun"})
print(f"\n[Test 4] Auth Me (Authorization: Bearer arjun):")
print(f"  Status: {status}, Resolved: {me_arjun['id']} ({me_arjun['name']})")
assert status == 200
assert me_arjun["id"] == "arjun"

# 5. Test GET /api/auth/me with invalid user (security check)
status, err = make_req("/auth/me", headers={"X-User-Id": "nonexistent_hacker"})
print(f"\n[Test 5] Security Check - Fake/Unregistered User:")
print(f"  Status: {status} (Expected 401), Detail: {err.get('detail')}")
assert status == 401

# 6. Test Chat endpoint with invalid user
status, chat_err = make_req("/chat", method="POST", headers={"X-User-Id": "intruder"}, body={"message": "hello"})
print(f"\n[Test 6] Chat Security Check - Intruder Blocked:")
print(f"  Status: {status} (Expected 401), Detail: {chat_err.get('detail')}")
assert status == 401

print("\n" + "=" * 60)
print("ALL AUTHENTICATION CHECKS PASSED SUCCESSFULLY!")
print("=" * 60)
