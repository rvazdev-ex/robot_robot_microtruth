from fastapi.testclient import TestClient

from trust_before_touch.api.app import create_app
from trust_before_touch.config import AppConfig
from trust_before_touch.constants import AttackMode, RuntimeBackend
from trust_before_touch.hardware.factory import create_adapters


def test_default_backend_is_simulation() -> None:
    config = AppConfig()
    assert config.runtime_backend == RuntimeBackend.SIMULATION


def test_factory_returns_simulation_adapters() -> None:
    config = AppConfig()
    leader, prover, verifier = create_adapters(
        config=config,
        backend=RuntimeBackend.SIMULATION,
        mode=AttackMode.NORMAL,
    )
    assert leader.__class__.__name__ == "SimLeaderArm"
    assert prover.__class__.__name__ == "SimProverArm"
    assert verifier.__class__.__name__ == "SimVerifierArm"


def test_api_returns_503_when_lerobot_runtime_is_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("TBT_RUNTIME_BACKEND", "lerobot")
    client = TestClient(create_app())
    session = client.post("/sessions", json={"attack_mode": "normal"}).json()
    sid = session["session_id"]

    assert client.post(f"/sessions/{sid}/claim", json={"message": "ok"}).status_code == 200
    challenge_response = client.post(f"/sessions/{sid}/challenge")
    assert challenge_response.status_code == 503
    assert "LeRobot backend requested" in challenge_response.json()["detail"]
