"""Simulated hardware backends for development and testing.

Implements both the new real-time RobotArm/RobotCamera interfaces and the
legacy PCS challenge-response interfaces.
"""

from __future__ import annotations

import math
import time
from random import Random

from trust_before_touch.constants import AttackMode, ChallengeType
from trust_before_touch.hardware.interfaces import (
    Camera,
    LeaderArm,
    ProverArm,
    RobotArm,
    RobotCamera,
    VerifierArm,
)
from trust_before_touch.models.protocol import Challenge, TelemetrySnapshot
from trust_before_touch.models.robot import (
    NUM_JOINTS,
    ArmTelemetry,
    CameraFrame,
    JointState,
)
from trust_before_touch.protocol.challenges import ChallengeGenerator
from trust_before_touch.simulation.engine import SimulationEngine

# ---------------------------------------------------------------------------
# Simulated real-time arm
# ---------------------------------------------------------------------------


class SimRobotArm(RobotArm):
    """Simulated arm with smooth sinusoidal joint motion."""

    def __init__(self, name: str, seed: int = 42) -> None:
        self._name = name
        self._connected = False
        self._positions = [0.0] * NUM_JOINTS
        self._velocities = [0.0] * NUM_JOINTS
        self._rng = Random(seed)
        self._start_time = time.time()
        self._is_leader = "leader" in name

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        self._connected = True
        self._start_time = time.time()

    def disconnect(self) -> None:
        self._connected = False

    def read_joints(self) -> JointState:
        if self._is_leader:
            # Simulate organic leader motion with slow sinusoids
            t = time.time() - self._start_time
            self._positions = [
                30.0 * math.sin(0.5 * t + i * 0.7) for i in range(NUM_JOINTS)
            ]
            self._velocities = [
                30.0 * 0.5 * math.cos(0.5 * t + i * 0.7) for i in range(NUM_JOINTS)
            ]
        return JointState(
            positions=list(self._positions),
            velocities=list(self._velocities),
            timestamp=time.time(),
        )

    def write_joints(self, positions: list[float]) -> None:
        old = self._positions
        self._velocities = [
            (p - o) * 30.0 for p, o in zip(positions, old, strict=False)
        ]  # approx velocity at 30Hz
        self._positions = list(positions)

    def get_telemetry(self) -> ArmTelemetry:
        js = self.read_joints()
        return ArmTelemetry(
            arm_name=self._name,
            joint_state=js,
            is_moving=any(abs(v) > 0.5 for v in js.velocities),
            temperature=[35.0 + self._rng.gauss(0, 1) for _ in range(NUM_JOINTS)],
            load=[self._rng.gauss(0, 5) for _ in range(NUM_JOINTS)],
        )


# ---------------------------------------------------------------------------
# Simulated camera
# ---------------------------------------------------------------------------


class SimRobotCamera(RobotCamera):
    """Simulated camera returning placeholder frames."""

    def __init__(self, device: str = "/dev/video0") -> None:
        self._device = device
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def capture_frame(self) -> CameraFrame:
        return CameraFrame(
            width=640,
            height=480,
            channels=3,
            timestamp=time.time(),
            device=self._device,
            data_b64=None,
        )


# ---------------------------------------------------------------------------
# Legacy PCS adapters (unchanged interface)
# ---------------------------------------------------------------------------


class SimLeaderArm(LeaderArm):
    def __init__(self, generator: ChallengeGenerator) -> None:
        self.generator = generator

    def generate_challenge(self, challenge_type: ChallengeType | None = None) -> Challenge:
        return self.generator.generate(challenge_type)


class SimProverArm(ProverArm):
    def __init__(self) -> None:
        self.last_positions: list[float] = []

    def execute_challenge(self, challenge: Challenge) -> None:
        self.last_positions = list(challenge.trajectory_points)


class SimCamera(Camera):
    def capture_frame(self) -> dict[str, float | str]:
        return {"marker": "object-A", "confidence": 0.95}


class SimVerifierArm(VerifierArm):
    def __init__(self, engine: SimulationEngine, mode: AttackMode):
        self.engine = engine
        self.mode = mode

    def observe_execution(self, challenge: Challenge) -> TelemetrySnapshot:
        return self.engine.run(challenge, self.mode)
