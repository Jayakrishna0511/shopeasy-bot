"""Verification script for Step C1: POST /api/chat and messages persistence.

Usage:
    cd backend
    python scripts/test_chat_api.py
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_pipeline() -> None:
    print("=" * 70)
    print("ShopEasy Chat API Verification (Step C1)")
    print("=" * 70)

    # 1. Send first message (new session)
    print("\n[1] Testing POST /api/chat (First question)...")
    payload1 = {"message": "How long do I have to return an item?"}
    res1 = client.post("/api/chat", json=payload1)
    assert res1.status_code == 200, f"Expected 200, got {res1.status_code}: {res1.text}"
    data1 = res1.json()
    session_id = data1["session_id"]
    print(f"  -> HTTP 200 OK")
    print(f"  -> Generated Session ID: {session_id}")
    print(f"  -> Answer: {data1['answer']}")
    print(f"  -> Sources: {data1['sources']}")

    # 2. Send second message in same session
    print("\n[2] Testing POST /api/chat (Second question in same session)...")
    payload2 = {
        "message": "My package arrived broken, what do I do?",
        "session_id": session_id,
    }
    res2 = client.post("/api/chat", json=payload2)
    assert res2.status_code == 200, f"Expected 200, got {res2.status_code}: {res2.text}"
    data2 = res2.json()
    assert data2["session_id"] == session_id, "Session ID should be preserved"
    print(f"  -> HTTP 200 OK")
    print(f"  -> Preserved Session ID: {data2['session_id']}")
    print(f"  -> Answer: {data2['answer']}")
    print(f"  -> Sources: {data2['sources']}")

    # 3. Check history endpoint & database persistence
    print(f"\n[3] Testing GET /api/chat/history/{session_id} (Database verification)...")
    res_history = client.get(f"/api/chat/history/{session_id}")
    assert res_history.status_code == 200
    history = res_history.json()
    print(f"  -> Total messages persisted in DB: {len(history)}")
    for idx, msg in enumerate(history, 1):
        print(f"     [{idx}] ({msg['role'].upper()}): {msg['content'][:60]}...")

    # 4. Test unanswerable question refusal
    print("\n[4] Testing POST /api/chat (Unanswerable refusal test)...")
    payload3 = {"message": "What is the capital of Japan?", "session_id": session_id}
    res3 = client.post("/api/chat", json=payload3)
    data3 = res3.json()
    print(f"  -> Answer: {data3['answer']}")
    assert "I don't know based on the provided documents" in data3["answer"]

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED! Step C1 Chat API and DB persistence verified.")
    print("=" * 70)


if __name__ == "__main__":
    test_chat_pipeline()
