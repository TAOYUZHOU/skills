from fastapi.testclient import TestClient

from app import app


def test_health() -> None:
    r = TestClient(app).get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_state_shape() -> None:
    r = TestClient(app).get("/api/state")
    assert r.status_code == 200
    body = r.json()
    assert "frontier" in body and "history" in body and "budget" in body


def test_record_iteration() -> None:
    c = TestClient(app)
    r = c.post("/api/iterations", json={
        "hypothesis": "health endpoint returns ok",
        "diff_summary": "tests only",
        "evidence": ["evidence/self-check.json"],
        "result": "verified",
    })
    assert r.status_code == 200
    assert r.json()["recorded"]["hypothesis"].startswith("health")
