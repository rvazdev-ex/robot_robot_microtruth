"""Real-time control loop for leader-follower teleoperation.

Reads the leader arm joint positions at a fixed frequency and commands
follower arm(s) to mirror those positions. Streams telemetry to registered
listeners via async callbacks.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from typing import Any, Callable, Coroutine

from trust_before_touch.config import AppConfig
from trust_before_touch.constants import ControlMode
from trust_before_touch.hardware.interfaces import RobotArm, RobotCamera
from trust_before_touch.models.robot import (
    ArmTelemetry,
    CameraFrame,
    JointState,
    RobotState,
    TrajectoryPoint,
    TrajectoryRecording,
)

logger = logging.getLogger(__name__)

TelemetryCallback = Callable[[RobotState], Coroutine[Any, Any, None]]


class RealtimeControlLoop:
    """Async control loop that drives leader-follower teleoperation at a fixed frequency.

    Usage:
        loop = RealtimeControlLoop(config, leader, [follower_left, follower_right], camera)
        loop.on_telemetry(my_callback)
        await loop.start()    # starts the control task
        await loop.stop()     # gracefully stops
    """

    def __init__(
        self,
        config: AppConfig,
        leader: RobotArm,
        followers: list[RobotArm],
        camera: RobotCamera | None = None,
    ) -> None:
        self.config = config
        self.leader = leader
        self.followers = followers
        self.camera = camera

        self._mode = ControlMode.IDLE
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._callbacks: list[TelemetryCallback] = []

        # Telemetry state
        self._latest_state = RobotState()
        self._loop_dt_history: deque[float] = deque(maxlen=100)
        self._recording: TrajectoryRecording | None = None

        # Safety
        self._max_delta = config.max_joint_delta_deg

    # -- Public API ----------------------------------------------------------

    @property
    def mode(self) -> ControlMode:
        return self._mode

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def latest_state(self) -> RobotState:
        return self._latest_state

    @property
    def recording(self) -> TrajectoryRecording | None:
        return self._recording

    def on_telemetry(self, callback: TelemetryCallback) -> None:
        self._callbacks.append(callback)

    async def connect_all(self) -> None:
        """Connect all arms and camera."""
        self.leader.connect()
        for f in self.followers:
            f.connect()
        if self.camera is not None:
            self.camera.connect()
        logger.info(
            "All hardware connected: leader=%s, followers=%s",
            self.leader.name,
            [f.name for f in self.followers],
        )

    async def disconnect_all(self) -> None:
        """Disconnect all hardware."""
        for f in self.followers:
            f.disconnect()
        self.leader.disconnect()
        if self.camera is not None:
            self.camera.disconnect()
        logger.info("All hardware disconnected")

    async def start(self, mode: ControlMode = ControlMode.TELEOPERATION) -> None:
        """Start the control loop."""
        if self._running:
            logger.warning("Control loop already running")
            return
        self._mode = mode
        self._running = True
        if mode == ControlMode.RECORDING:
            self._recording = TrajectoryRecording(start_time=time.time())
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Control loop started in %s mode at %.1f Hz", mode, self.config.control_frequency_hz)

    async def stop(self) -> None:
        """Stop the control loop gracefully."""
        self._running = False
        if self._task is not None:
            try:
                await asyncio.wait_for(self._task, timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._task.cancel()
            self._task = None
        if self._recording is not None:
            self._recording.end_time = time.time()
        self._mode = ControlMode.IDLE
        logger.info("Control loop stopped")

    # -- Internal loop -------------------------------------------------------

    async def _run_loop(self) -> None:
        dt = self.config.control_dt
        telemetry_interval = self.config.telemetry_dt
        last_telemetry_push = 0.0

        while self._running:
            loop_start = time.time()

            try:
                # 1. Read leader joints
                leader_joints = self.leader.read_joints()

                # 2. Command followers (with safety clamping)
                follower_telemetry: list[ArmTelemetry] = []
                for follower in self.followers:
                    if self._mode in (ControlMode.TELEOPERATION, ControlMode.RECORDING):
                        clamped = self._safety_clamp(leader_joints.positions, follower)
                        follower.write_joints(clamped)

                    ft = follower.get_telemetry()
                    follower_telemetry.append(ft)

                # 3. Record if in recording mode
                if self._mode == ControlMode.RECORDING and self._recording is not None:
                    if follower_telemetry:
                        self._recording.points.append(
                            TrajectoryPoint(
                                leader_positions=leader_joints.positions,
                                follower_positions=follower_telemetry[0].joint_state.positions,
                                timestamp=time.time(),
                            )
                        )

                # 4. Capture camera frame (at reduced rate)
                camera_frame: CameraFrame | None = None
                if self.camera is not None and self.camera.is_connected:
                    now = time.time()
                    if now - last_telemetry_push >= telemetry_interval:
                        camera_frame = self.camera.capture_frame()

                # 5. Build aggregated state
                loop_elapsed = time.time() - loop_start
                self._loop_dt_history.append(loop_elapsed)
                avg_dt = sum(self._loop_dt_history) / len(self._loop_dt_history)

                state = RobotState(
                    leader=self.leader.get_telemetry(),
                    follower_left=follower_telemetry[0] if len(follower_telemetry) > 0 else None,
                    follower_right=follower_telemetry[1] if len(follower_telemetry) > 1 else None,
                    camera_frame=camera_frame,
                    control_active=True,
                    control_frequency_hz=1.0 / avg_dt if avg_dt > 0 else 0.0,
                    loop_dt_ms=loop_elapsed * 1000.0,
                    timestamp=time.time(),
                )
                self._latest_state = state

                # 6. Push telemetry at reduced rate
                now = time.time()
                if now - last_telemetry_push >= telemetry_interval:
                    last_telemetry_push = now
                    await self._push_telemetry(state)

            except Exception:
                logger.exception("Control loop error")

            # Sleep to maintain target frequency
            elapsed = time.time() - loop_start
            sleep_time = max(0.0, dt - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    def _safety_clamp(self, target: list[float], follower: RobotArm) -> list[float]:
        """Clamp position deltas to prevent dangerous fast movements."""
        current = follower.read_joints().positions
        clamped: list[float] = []
        for t, c in zip(target, current):
            delta = t - c
            if abs(delta) > self._max_delta:
                delta = self._max_delta if delta > 0 else -self._max_delta
            clamped.append(c + delta)
        return clamped

    async def _push_telemetry(self, state: RobotState) -> None:
        for cb in self._callbacks:
            try:
                await cb(state)
            except Exception:
                logger.exception("Telemetry callback error")
