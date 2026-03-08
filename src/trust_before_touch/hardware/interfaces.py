"""Hardware interface protocols for real-time robot control.

Defines the contracts that both simulated and real LeRobot backends must implement.
The legacy challenge-response protocols are kept for backward compatibility with the
PCS verification layer, but the primary interfaces are now real-time oriented.
"""

from __future__ import annotations

from typing import Protocol

from trust_before_touch.constants import ChallengeType
from trust_before_touch.models.protocol import Challenge, TelemetrySnapshot
from trust_before_touch.models.robot import ArmTelemetry, CameraFrame, JointState

# ---------------------------------------------------------------------------
# Real-time robot arm interface
# ---------------------------------------------------------------------------


class RobotArm(Protocol):
    """Real-time interface to a single SO-101 arm."""

    @property
    def name(self) -> str:
        """Arm identifier (e.g. 'leader', 'follower_left', 'follower_right')."""
        ...

    @property
    def is_connected(self) -> bool:
        ...

    def connect(self) -> None:
        ...

    def disconnect(self) -> None:
        ...

    def read_joints(self) -> JointState:
        """Read current joint positions/velocities from the arm."""
        ...

    def write_joints(self, positions: list[float]) -> None:
        """Command target joint positions (follower arms only)."""
        ...

    def get_telemetry(self) -> ArmTelemetry:
        """Get full telemetry snapshot including load/temperature."""
        ...


class RobotCamera(Protocol):
    """Real-time camera interface."""

    @property
    def is_connected(self) -> bool:
        ...

    def connect(self) -> None:
        ...

    def disconnect(self) -> None:
        ...

    def capture_frame(self) -> CameraFrame:
        """Capture a single frame."""
        ...


# ---------------------------------------------------------------------------
# Legacy PCS challenge-response interfaces (kept for verification layer)
# ---------------------------------------------------------------------------


class LeaderArm(Protocol):
    def generate_challenge(self, challenge_type: ChallengeType | None = None) -> Challenge:
        ...


class ProverArm(Protocol):
    def execute_challenge(self, challenge: Challenge) -> None:
        ...


class VerifierArm(Protocol):
    def observe_execution(self, challenge: Challenge) -> TelemetrySnapshot:
        ...


class Camera(Protocol):
    def capture_frame(self) -> dict[str, float | str]:
        ...
