# 🤖 Trust Before Touch (SO-101)

> **Simulation-first real-time teleoperation + physical challenge-response trust verification** for SO-101 robotic arms.

[![Python](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](#)
[![Lint: Ruff](https://img.shields.io/badge/lint-ruff-46a758)](#development)
[![Type check: mypy](https://img.shields.io/badge/types-mypy-2f5d95)](#development)
[![Tests: pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)](#development)

---

## ✨ What this project does

`trust-before-touch-so101` provides a complete stack for **leader–follower robot control** and **trust scoring**:

- Real-time teleoperation loop (default 30 Hz)
- Live telemetry over WebSocket for dashboard visualization
- Trajectory recording for replay and analysis
- Safety clamping on per-step joint movement
- PCS-style challenge/execute/verify trust sessions
- Dual runtime backends:
  - **Simulation** (default, deterministic development)
  - **LeRobot hardware** (SO-101 + camera)

---

## 🧠 System architecture

```text
Leader Arm (SO-101) ──read joints──▶ Realtime Control Loop ──write joints──▶ Follower Arm(s)
                                          │
                                          ├── Telemetry State ──▶ WS /ws/telemetry ──▶ Dashboard
                                          │
                                          └── PCS Session Engine ──▶ Trust Score
```

### Main modules

- `src/trust_before_touch/control` — realtime control loop
- `src/trust_before_touch/hardware` — hardware interfaces + simulation/LeRobot adapters
- `src/trust_before_touch/protocol` — session/challenge orchestration
- `src/trust_before_touch/scoring` — trust score computation
- `src/trust_before_touch/api` — FastAPI app + WebSocket + dashboard route
- `src/trust_before_touch/cli` — Typer CLI commands

---

## ✅ Requirements

- **Python 3.12+**
- Optional: LeRobot-compatible SO-101 hardware and camera for physical runs

---

## 📦 Installation

```bash
# core (simulation-first)
pip install -e .[dev]

# with LeRobot extras
pip install -e .[dev,lerobot]
```

---

## 🚀 Quick start

### 1) Simulation mode (recommended)

```bash
make dev
```

Then open: <http://localhost:8000>

You can also run teleoperation in terminal:

```bash
make teleoperate-sim
```

### 2) Hardware mode (LeRobot)

```bash
export TBT_RUNTIME_BACKEND=lerobot
make teleoperate
```

Other useful commands:

```bash
make read-joints
make dev
```

---

## 🖥️ CLI usage

```bash
# Teleoperate (Ctrl+C to stop)
trust-before-touch teleoperate --backend lerobot

# Record trajectory for N seconds
trust-before-touch record --backend lerobot --duration 10

# Read current joints
trust-before-touch read-joints --backend lerobot
```

### PCS demo commands

```bash
trust-before-touch run-demo --mode normal --backend lerobot
trust-before-touch run-demo --mode replay
trust-before-touch run-demo --mode delay
trust-before-touch run-training-watermark-demo
trust-before-touch run-cross-camera-watermark-demo
```

---

## 🌐 API reference

### Health and config

- `GET /health` — service health
- `GET /config` — active runtime configuration
- `GET /` — dashboard UI

### Realtime control

- `POST /control/start?mode=teleoperation`
- `POST /control/stop`
- `GET /control/state`
- `GET /control/recording`
- `WS /ws/telemetry`

### PCS sessions

- `POST /sessions`
- `POST /sessions/{id}/claim`
- `POST /sessions/{id}/challenge`
- `POST /sessions/{id}/execute`
- `POST /sessions/{id}/verify`
- `GET /sessions/{id}/score`

---

## ⚙️ Configuration

All env vars are prefixed with `TBT_`.

```bash
# Runtime
TBT_RUNTIME_BACKEND=simulation   # simulation | lerobot

# Loop rates
TBT_CONTROL_FREQUENCY_HZ=30.0
TBT_TELEMETRY_FREQUENCY_HZ=10.0

# Safety
TBT_MAX_JOINT_DELTA_DEG=5.0

# Hardware ports (LeRobot)
TBT_LEROBOT_LEADER_ARM_PORT=/dev/ttyACM1
TBT_LEROBOT_FOLLOWER_WITH_CAMERA_PORT=/dev/ttyACM0
TBT_LEROBOT_FOLLOWER_WITHOUT_CAMERA_PORT=/dev/ttyACM2
TBT_LEROBOT_CAMERA_DEVICE=/dev/video2
TBT_LEROBOT_MOTOR_MODEL=sts3215

# Followers
TBT_ENABLE_FOLLOWER_LEFT=true
TBT_ENABLE_FOLLOWER_RIGHT=true
```

Default config file: `configs/default.toml`

---

## 🦾 Hardware layout (expected)

| Component | Default device | Role |
|---|---|---|
| Leader arm | `/dev/ttyACM1` | Human-driven source joints |
| Follower left | `/dev/ttyACM0` | Mirror + camera host |
| Follower right | `/dev/ttyACM2` | Mirror |
| Camera | `/dev/video2` | Scene observation |

SO-101 joint order:

1. `shoulder_pan`
2. `shoulder_lift`
3. `elbow_flex`
4. `wrist_flex`
5. `wrist_roll`
6. `gripper`

---

## 🧪 Development

```bash
make install      # install with dev deps
make format       # ruff format
make lint         # ruff check
make typecheck    # mypy
make test         # pytest
```

Suggested pre-merge check:

```bash
make format && make lint && make typecheck && make test
```

---

## 📚 Documentation

See `docs/` for deeper technical references:

- `docs/architecture.md`
- `docs/hardware-integration.md`
- `docs/protocol.md`
- `docs/threat-model.md`
- `docs/demo-runbook.md`

---

## 📄 License

MIT — see `LICENSE`.
