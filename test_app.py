"""
Automated End-to-End Verification Test for OnCall Memory.
Exercises all REST endpoints using FastAPI TestClient:
1. UI root index.html
2. Samples and scenarios API
3. Memory bank stats and list
4. Side-by-side incident analysis
5. Feedback loop retention
6. Hindsight Reflect insights
"""

import sys
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_all():
    print("Testing OnCall Memory End-to-End...")
    
    # 1. UI Root
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200 on /, got {res.status_code}"
    assert "OnCall Memory" in res.text
    print("PASS: GET / (UI HTML served)")

    # 2. Samples and Scenarios
    res = client.get("/api/samples")
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("samples", [])) >= 3
    assert len(data.get("scenarios", [])) >= 3
    print(f"PASS: GET /api/samples ({len(data['samples'])} samples, {len(data['scenarios'])} scenarios)")

    # 3. Memory Stats
    res = client.get("/api/memories/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats.get("total_memories") is not None
    assert stats.get("bank_id") == "northwind-oncall"
    print(f"PASS: GET /api/memories/stats (Bank: {stats['bank_id']}, Count: {stats['total_memories']})")

    # 4. Memory List
    res = client.get("/api/memories/list?limit=10")
    assert res.status_code == 200
    mem_list = res.json()
    assert len(mem_list.get("items", [])) > 0
    print(f"PASS: GET /api/memories/list ({len(mem_list['items'])} items returned)")

    # 5. Side-by-Side Incident Analysis
    payload = {
        "alert": "P1 ALERT: Checkout Service Connection Pool Exhaustion",
        "logs": "[checkout-service] FATAL: remaining connection slots are reserved for non-replication superuser connections\nConnectionPoolExhausted: Pool max_connections=200 reached.",
        "service": "checkout-service"
    }
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200, f"Analyze failed: {res.text}"
    analysis = res.json()
    assert "without_memory" in analysis
    assert "with_memory" in analysis
    assert analysis["without_memory"]["confidence"] != ""
    assert analysis["with_memory"]["confidence"] != ""
    assert len(analysis["with_memory"].get("citations", [])) > 0
    print("PASS: POST /api/analyze (Side-by-side comparison verified with citations)")

    # 6. Feedback Loop Retention
    feedback_payload = {
        "alert": payload["alert"],
        "logs": payload["logs"],
        "service": "checkout-service",
        "fix_status": "SUCCESS",
        "solution_notes": "Terminated idle backend handles and scaled PgBouncer pool.",
        "suggested_root_cause": analysis["with_memory"]["root_cause"]
    }
    res = client.post("/api/feedback", json=feedback_payload)
    assert res.status_code == 200
    fb_res = res.json()
    assert fb_res.get("status") == "success"
    print(f"PASS: POST /api/feedback (Retained memory ID: {fb_res.get('incident_id')})")

    # 7. Hindsight Reflect Insights
    res = client.post("/api/insights", json={"query": "What patterns keep causing our incidents and what should we fix permanently?"})
    assert res.status_code == 200
    insights = res.json()
    assert "reflection" in insights
    assert len(insights["reflection"]) > 100
    print("PASS: POST /api/insights (Reflect synthesis generated)")

    print("\nALL 7 END-TO-END TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_all()
