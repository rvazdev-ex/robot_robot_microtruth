from fastapi.testclient import TestClient

from trust_before_touch.api.app import create_app


def test_api_happy_path() -> None:
    client = TestClient(create_app())
    res = client.get("/health")
    assert res.status_code == 200

    session = client.post("/sessions", json={"attack_mode": "normal"}).json()
    sid = session["session_id"]

    assert client.post(f"/sessions/{sid}/claim", json={"message": "ok"}).status_code == 200
    assert client.post(f"/sessions/{sid}/challenge").status_code == 200
    assert client.post(f"/sessions/{sid}/execute", json={}).status_code == 200
    final = client.post(f"/sessions/{sid}/verify").json()
    assert final["state"] in {"passed", "failed"}
    score = client.get(f"/sessions/{sid}/score").json()
    assert "total" in score
