"""Real-time robot control models for SO-101 arms."""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field


# SO-101 has 6 joints: shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper
SO101_JOINT_NAMES = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]

NUM_JOINTS = len(SO101_JOINT_NAMES)


class JointState(BaseModel):
    """Position state for all 6 joints of an SO-101 arm (in degrees)."""

    positions: list[float] = Field(default_factory=lambda: [0.0] * NUM_JOINTS)
    velocities: list[float] = Field(default_factory=lambda: [0.0] * NUM_JOINTS)
    timestamp: float = Field(default_factory=time.time)

    @property
    def as_dict(self) -> dict[str, float]:
        return dict(zip(SO101_JOINT_NAMES, self.positions))


class ArmTelemetry(BaseModel):
    """Real-time telemetry snapshot from one arm."""

    arm_name: str
    joint_state: JointState
    is_moving: bool = False
    temperature: list[float] = Field(default_factory=lambda: [0.0] * NUM_JOINTS)
    load: list[float] = Field(default_factory=lambda: [0.0] * NUM_JOINTS)


class ControlCommand(BaseModel):
    """Command to send target joint positions to a follower arm."""

    target_positions: list[float] = Field(default_factory=lambda: [0.0] * NUM_JOINTS)
    duration_ms: int = 0


class RobotState(BaseModel):
    """Aggregated state of the full 3-arm robot system."""

    leader: ArmTelemetry | None = None
    follower_left: ArmTelemetry | None = None
    follower_right: ArmTelemetry | None = None
    camera_frame: CameraFrame | None = None
    control_active: bool = False
    control_frequency_hz: float = 0.0
    loop_dt_ms: float = 0.0
    timestamp: float = Field(default_factory=time.time)


class CameraFrame(BaseModel):
    """A captured camera frame with metadata."""

    width: int = 640
    height: int = 480
    channels: int = 3
    timestamp: float = Field(default_factory=time.time)
    device: str = ""
    data_b64: str | None = None  # base64-encoded JPEG for streaming
    detections: list[dict[str, Any]] = Field(default_factory=list)


# Fix forward reference
RobotState.model_rebuild()


class TrajectoryPoint(BaseModel):
    """A single point in a recorded trajectory."""

    leader_positions: list[float]
    follower_positions: list[float]
    timestamp: float


class TrajectoryRecording(BaseModel):
    """A recorded trajectory for replay or verification."""

    points: list[TrajectoryPoint] = Field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    follower_arm: str = "left"

    @property
    def duration_ms(self) -> float:
        if not self.points:
            return 0.0
        return (self.end_time - self.start_time) * 1000.0

    @property
    def num_points(self) -> int:
        return len(self.points)

    def tracking_error(self) -> float:
        """Compute mean absolute tracking error between leader and follower."""
        if not self.points:
            return 0.0
        total = 0.0
        for pt in self.points:
            for lp, fp in zip(pt.leader_positions, pt.follower_positions):
                total += abs(lp - fp)
        return total / (len(self.points) * NUM_JOINTS)
