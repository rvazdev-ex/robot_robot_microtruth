# trust-before-touch-so101

Real-time robot manipulation and control for a 3-arm SO-101 setup with LeRobot integration and physical challenge-response (PCS) verification.

## Overview

This project provides **real-time leader-follower teleoperation** for SO-101 robotic arms via LeRobot, with an integrated trust verification layer. The leader arm drives one or two follower arms at configurable control frequencies (default 30 Hz), with live 6-DOF joint streaming via WebSocket.

### Key capabilities

- **Real-time teleoperation**: Read leader arm joints and mirror to follower arm(s) at 30 Hz
- **Live telemetry dashboard**: 6-DOF joint visualization for all 3 arms via WebSocket
- **Trajectory recording**: Record leader-follower trajectories for replay and training
- **Safety clamping**: Configurable max joint velocity to prevent dangerous movements
- **PCS verification**: Physical challenge-response protocol for trust scoring
- **Dual backend**: Simulation mode for development, LeRobot mode for real hardware

## Architecture

```
Leader Arm (SO-101)  ──read joints──▶  Control Loop (30 Hz)  ──write joints──▶  Follower Arms
                                            │
                                       telemetry (10 Hz)
                                            │
                                     WebSocket /ws/telemetry ──▶  Dashboard (6-DOF viz)
                                            │
                                     PCS Verification Layer ──▶  Trust Scoring
```

- **Control loop**: Async real-time loop reading leader, commanding followers, pushing telemetry
- **Hardware layer**: `RobotArm` / `RobotCamera` protocols with LeRobot + simulation backends
- **FastAPI backend**: REST + WebSocket for control, telemetry streaming, and PCS sessions
- **Dashboard**: Real-time 6-DOF joint bar visualization at `/`

## Installation

```bash
# Core (simulation mode)
pip install -e .[dev]

# With LeRobot hardware support
pip install -e .[dev,lerobot]
```

## Quick start

### Simulation mode
```bash
# Start the dashboard + API server
make dev

# Or run teleoperation in the terminal (simulated)
make teleoperate-sim
```

### Real hardware (LeRobot)
```bash
# Set the backend to lerobot
export TBT_RUNTIME_BACKEND=lerobot

# Start teleoperation
make teleoperate

# Or read current joint positions
make read-joints

# Or start the dashboard
make dev
```

Open http://localhost:8000 for the real-time dashboard.

## CLI commands

### Real-time control
```bash
# Leader-follower teleoperation (Ctrl+C to stop)
trust-before-touch teleoperate --backend lerobot

# Record a 10-second trajectory
trust-before-touch record --backend lerobot --duration 10

# Read current joint positions from all arms
trust-before-touch read-joints --backend lerobot
```

### PCS verification
```bash
trust-before-touch run-demo --mode normal --backend lerobot
trust-before-touch run-demo --mode replay
trust-before-touch run-demo --mode delay
trust-before-touch run-training-watermark-demo
trust-before-touch run-cross-camera-watermark-demo
```

## API endpoints

### Real-time control
- `POST /control/start?mode=teleoperation` — Connect hardware, start control loop
- `POST /control/stop` — Stop control loop, disconnect hardware
- `GET /control/state` — Latest aggregated robot state (all arms + camera)
- `GET /control/recording` — Current trajectory recording stats
- `WS /ws/telemetry` — Real-time joint telemetry stream

### PCS sessions
- `POST /sessions` — Create verification session
- `POST /sessions/{id}/claim` — Prover claims readiness
- `POST /sessions/{id}/challenge` — Leader issues challenge
- `POST /sessions/{id}/execute` — Prover executes
- `POST /sessions/{id}/verify` — Verifier scores
- `GET /sessions/{id}/score` — Get trust score

### General
- `GET /health` — Health check
- `GET /config` — Current configuration
- `GET /` — Real-time dashboard

## Configuration

All settings are configurable via environment variables (prefix `TBT_`):

```bash
# Runtime backend
TBT_RUNTIME_BACKEND=lerobot          # "simulation" or "lerobot"

# Control parameters
TBT_CONTROL_FREQUENCY_HZ=30.0       # Control loop frequency
TBT_TELEMETRY_FREQUENCY_HZ=10.0     # WebSocket push rate
TBT_MAX_JOINT_DELTA_DEG=5.0         # Safety: max degrees per step

# LeRobot hardware ports
TBT_LEROBOT_LEADER_ARM_PORT=/dev/ttyACM1
TBT_LEROBOT_FOLLOWER_WITH_CAMERA_PORT=/dev/ttyACM0
TBT_LEROBOT_FOLLOWER_WITHOUT_CAMERA_PORT=/dev/ttyACM2
TBT_LEROBOT_CAMERA_DEVICE=/dev/video2
TBT_LEROBOT_MOTOR_MODEL=sts3215

# Enable/disable follower arms
TBT_ENABLE_FOLLOWER_LEFT=true
TBT_ENABLE_FOLLOWER_RIGHT=true
```

## Hardware setup

The system expects 3 SO-101 arms with Feetech STS3215 servos, already calibrated via LeRobot:

| Arm | Default Port | Role |
|-----|-------------|------|
| Leader | `/dev/ttyACM1` | Reads joint positions (human-controlled) |
| Follower Left | `/dev/ttyACM0` | Mirrors leader + has camera |
| Follower Right | `/dev/ttyACM2` | Mirrors leader (no camera) |
| Camera | `/dev/video2` | Mounted on follower left |

Each arm has 6 joints: `shoulder_pan`, `shoulder_lift`, `elbow_flex`, `wrist_flex`, `wrist_roll`, `gripper`.

## Development

```bash
make install        # Install with dev deps
make test           # Run pytest
make lint           # Run ruff
make typecheck      # Run mypy
make format         # Auto-format
make dev            # Start dev server with hot reload
```
