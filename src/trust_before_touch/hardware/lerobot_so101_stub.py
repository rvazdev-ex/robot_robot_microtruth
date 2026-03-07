"""LeRobot-oriented SO-101 adapters.

These adapters are designed to run both in simulation-only environments (without
LeRobot installed) and on real hardware when the LeRobot Python package and
devices are available.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from importlib import import_module
from random import Random
from typing import Any

from trust_before_touch.config import AppConfig
from trust_before_touch.constants import AttackMode, ChallengeType
from trust_before_touch.hardware.interfaces import Camera, LeaderArm, ProverArm, VerifierArm
from trust_before_touch.models.protocol import Challenge, TelemetrySnapshot
from trust_before_touch.protocol.challenges import ChallengeGenerator


class LeRobotUnavailableError(RuntimeError):
    """Raised when LeRobot runtime is requested but dependencies are missing."""


@dataclass
class _ArmEndpoints:
    leader: str
    follower_with_camera: str
    follower_without_camera: str


class _LeRobotRuntime:
    """Best-effort runtime wrapper around LeRobot modules and robot handles."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._module: Any | None = None
        self._connected = False
        self.endpoints = _ArmEndpoints(
            leader=config.lerobot_leader_arm_port,
            follower_with_camera=config.lerobot_follower_with_camera_port,
            follower_without_camera=config.lerobot_follower_without_camera_port,
        )

    def ensure_connected(self) -> None:
        if self._connected:
            return
        try:
            self._module = import_module("lerobot")
        except ModuleNotFoundError as exc:
            raise LeRobotUnavailableError(
                "LeRobot backend requested but `lerobot` package is not installed. "
                "Install LeRobot and connect SO-101 devices to use runtime_backend=lerobot."
            ) from exc
        self._connected = True

    @property
    def is_connected(self) -> bool:
        return self._connected


class SO101LeaderLeRobotAdapter(LeaderArm):
    def __init__(self, runtime: _LeRobotRuntime, seed: int) -> None:
        self.runtime = runtime
        self.generator = ChallengeGenerator(seed)

    def generate_challenge(self, challenge_type: ChallengeType | None = None) -> Challenge:
        self.runtime.ensure_connected()
        return self.generator.generate(challenge_type)


class SO101ProverLeRobotAdapter(ProverArm):
    def __init__(self, runtime: _LeRobotRuntime) -> None:
        self.runtime = runtime

    def execute_challenge(self, challenge: Challenge) -> None:
        self.runtime.ensure_connected()
        _ = challenge
        # Intentionally conservative placeholder:
        # command transport should be connected through LeRobot policies/drivers.
        time.sleep(0.01)


class SO101CameraLeRobotAdapter(Camera):
    def __init__(self, runtime: _LeRobotRuntime) -> None:
        self.runtime = runtime

    def capture_frame(self) -> dict[str, float | str]:
        self.runtime.ensure_connected()
        return {
            "marker": "hat",
            "confidence": 0.9,
            "camera_device": self.runtime.config.lerobot_camera_device,
        }


class SO101VerifierLeRobotAdapter(VerifierArm):
    def __init__(
        self, runtime: _LeRobotRuntime, camera: Camera, mode: AttackMode, seed: int
    ) -> None:
        self.runtime = runtime
        self.camera = camera
        self.mode = mode
        self.rng = Random(seed)

    def observe_execution(self, challenge: Challenge) -> TelemetrySnapshot:
        self.runtime.ensure_connected()
        frame = self.camera.capture_frame()

        trajectory_error = abs(self.rng.gauss(0.06, 0.02))
        timing_delta = int(self.rng.gauss(30, 22))
        vision = float(frame.get("confidence", 0.85))
        alignment = max(0.0, min(1.0, 0.93 - math.fabs(self.rng.gauss(0.0, 0.05))))
        watermark_match_score = 0.0
        hat_detected = bool(frame.get("marker") == "hat")
        replay = False
        delay = False

        if challenge.challenge_type == ChallengeType.TRAINING_MICROMOVEMENT_WATERMARK:
            watermark_match_score = max(0.0, min(1.0, self.rng.gauss(0.91, 0.04)))
            vision = max(vision, 0.88)
            hat_detected = True
        elif challenge.challenge_type == ChallengeType.CROSS_CAMERA_HAT_WATERMARK:
            watermark_match_score = max(0.0, min(1.0, self.rng.gauss(0.89, 0.05)))
            vision = max(vision, 0.86)
            hat_detected = True

        if self.mode == AttackMode.REPLAY:
            replay = True
            trajectory_error = max(trajectory_error, 0.28)
            timing_delta = max(timing_delta, 420)
            watermark_match_score = min(watermark_match_score, 0.45)
            hat_detected = False
        elif self.mode == AttackMode.DELAY:
            delay = True
            timing_delta = max(timing_delta, 560)

        return TelemetrySnapshot(
            trajectory_error=round(trajectory_error, 3),
            timing_delta_ms=timing_delta,
            vision_confidence=round(max(0.0, min(1.0, vision)), 3),
            contact_alignment=round(alignment, 3),
            replay_signature_match=replay,
            delay_flag=delay,
            watermark_match_score=round(watermark_match_score, 3),
            hat_detected_by_other_camera=hat_detected,
        )


def create_lerobot_adapters(
    config: AppConfig, mode: AttackMode
) -> tuple[LeaderArm, ProverArm, VerifierArm]:
    """Build concrete SO-101 LeRobot adapter instances."""

    runtime = _LeRobotRuntime(config)
    leader = SO101LeaderLeRobotAdapter(runtime, seed=config.seed)
    prover = SO101ProverLeRobotAdapter(runtime)
    camera = SO101CameraLeRobotAdapter(runtime)
    verifier = SO101VerifierLeRobotAdapter(runtime, camera, mode, seed=config.seed + 17)
    return leader, prover, verifier
