"""End-to-End verification script for Step D3: Agent Loop & Human Approval Flow."""

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


print("=" * 70)
print("Step D3: Agent Tool Loop & Approval Flow Verification")
print("=" * 70)

# 1. Test "list me my orders"
print("\n[Test 1] Customer asks: 'list me my orders' (as Ravi)")
status, resp1 = make_req("/chat", method="POST", headers={"X-User-Id": "ravi"}, body={"message": "list me my orders"})
print(f"  Status: {status}")
print(f"  Agent Answer:\n{resp1['answer'][:200]}...")
assert status == 200
assert "A100" in resp1["answer"]

# 2. Test "what is the status of order A1001?"
print("\n[Test 2] Customer asks: 'What is the status of order A1001?' (as Ravi)")
status, resp2 = make_req("/chat", method="POST", headers={"X-User-Id": "ravi"}, body={"message": "What is the status of order A1001?"})
print(f"  Status: {status}")
print(f"  Agent Answer:\n{resp2['answer']}")
assert status == 200
assert "A1001" in resp2["answer"]

# 3. Test "Cancel my order A1008" (A1008 is processing)
print("\n[Test 3] Customer requests cancellation: 'Please cancel my order A1008' (as Ravi)")
status, resp3 = make_req("/chat", method="POST", headers={"X-User-Id": "ravi"}, body={"message": "Please cancel my order A1008"})
print(f"  Status: {status}")
print(f"  Agent Answer:\n{resp3['answer']}")
print(f"  Approval Required Payload: {resp3.get('approval_required')}")
assert status == 200
assert resp3.get("approval_required") is not None
approval_token = resp3["approval_required"]["token"]
assert approval_token.startswith("appr_")

# 4. Security Check: Priya tries to approve Ravi's cancellation token
print("\n[Test 4] Security Check: Priya tries to approve Ravi's token")
status, intruder_resp = make_req("/approve", method="POST", headers={"X-User-Id": "priya"}, body={"token": approval_token})
print(f"  Status: {status} (Expected 403), Error: {intruder_resp.get('detail')}")
assert status == 403

# 5. Ravi approves his cancellation token
print("\n[Test 5] Ravi approves his own cancellation token")
status, approve_resp = make_req("/approve", method="POST", headers={"X-User-Id": "ravi"}, body={"token": approval_token})
print(f"  Status: {status}")
print(f"  Message: {approve_resp.get('message')}")
assert status == 200
assert approve_resp["success"] is True

# 6. Single-Use Check: Ravi tries to approve the same token again
print("\n[Test 6] Single-Use Check: Trying to reuse consumed approval token")
status, reuse_resp = make_req("/approve", method="POST", headers={"X-User-Id": "ravi"}, body={"token": approval_token})
print(f"  Status: {status} (Expected 400), Error: {reuse_resp.get('detail')}")
assert status == 400

print("\n" + "=" * 70)
print("ALL AGENT LOOP AND APPROVAL FLOW TESTS PASSED SUCCESSFULLY!")
print("=" * 70)
